import logging

from django.conf import settings
from django.db import transaction
from django.db.models import F, Prefetch, Sum

from constance import config
from rest_framework.exceptions import APIException

from aiarena.core.models import (
    BotCrashLimitAlert,
    CompetitionParticipation,
    Match,
    MatchParticipation,
    MatchTag,
    Tag,
)
from aiarena.core.services import Bots, BotStatistics
from aiarena.core.utils import parse_tags

from .serializers import (
    SubmitResultBotSerializer,
    SubmitResultParticipationSerializer,
    SubmitResultResultSerializer,
)


logger = logging.getLogger(__name__)


def handle_result_submission(match_id, result_data):
    with transaction.atomic():
        match = Match.objects.prefetch_related(
            Prefetch("matchparticipation_set", MatchParticipation.objects.all().select_related("bot"))
        ).get(id=match_id)
        # validate result
        result = SubmitResultResultSerializer(
            data={
                "match": match_id,
                "type": result_data["type"],
                "replay_file": result_data.get("replay_file"),
                "game_steps": result_data["game_steps"],
                "submitted_by": result_data["submitted_by"].pk,
                "arenaclient_log": result_data.get("arenaclient_log"),
            }
        )
        result.is_valid(raise_exception=True)
        # validate participants
        p1_instance = match.matchparticipation_set.get(participant_number=1)
        result_cause = p1_instance.calculate_result_cause(result_data["type"])
        participant1 = SubmitResultParticipationSerializer(
            instance=p1_instance,
            data={
                "avg_step_time": result_data.get("bot1_avg_step_time"),
                "match_log": result_data.get("bot1_log"),
                "result": p1_instance.calculate_relative_result(result_data["type"]),
                "result_cause": result_cause,
            },
            partial=True,
        )
        participant1.is_valid(raise_exception=True)
        p2_instance = match.matchparticipation_set.get(participant_number=2)
        participant2 = SubmitResultParticipationSerializer(
            instance=p2_instance,
            data={
                "avg_step_time": result_data.get("bot2_avg_step_time"),
                "match_log": result_data.get("bot2_log"),
                "result": p2_instance.calculate_relative_result(result_data["type"]),
                "result_cause": result_cause,
            },
            partial=True,
        )
        participant2.is_valid(raise_exception=True)
        # validate bots
        if not p1_instance.bot.is_in_match(match_id):
            logger.warning(
                f"A result was submitted for match {match_id}, " f"which Bot {p1_instance.bot.name} isn't currently in!"
            )
            raise APIException(f"Unable to log result: Bot {p1_instance.bot.name} is not currently in this match!")
        if not p2_instance.bot.is_in_match(match_id):
            logger.warning(
                f"A result was submitted for match {match_id}, " f"which Bot {p2_instance.bot.name} isn't currently in!"
            )
            raise APIException(f"Unable to log result: Bot {p2_instance.bot.name} is not currently in this match!")
        bot1 = None
        bot2 = None
        match_is_requested = match.is_requested
        # should we update the bot data?
        if p1_instance.use_bot_data and p1_instance.update_bot_data and not match_is_requested:
            bot1_data = result_data.get("bot1_data")
            # if we set the bot data key to anything, it will overwrite the existing bot data
            # so only include bot1_data if it isn't none
            # Also don't update bot data if it's a requested match.
            if bot1_data is not None and not match_is_requested:
                bot1_dict = {"bot_data": bot1_data}
                bot1 = SubmitResultBotSerializer(instance=p1_instance.bot, data=bot1_dict, partial=True)
                bot1.is_valid(raise_exception=True)
        if p2_instance.use_bot_data and p2_instance.update_bot_data and not match_is_requested:
            bot2_data = result_data.get("bot2_data")
            # if we set the bot data key to anything, it will overwrite the existing bot data
            # so only include bot2_data if it isn't none
            # Also don't update bot data if it's a requested match.
            if bot2_data is not None and not match_is_requested:
                bot2_dict = {"bot_data": bot2_data}
                bot2 = SubmitResultBotSerializer(instance=p2_instance.bot, data=bot2_dict, partial=True)
                bot2.is_valid(raise_exception=True)
        # save models
        result = result.save()
        participant1 = participant1.save()
        participant2 = participant2.save()
        # save these after the others so if there's a validation error,
        # then the bot data files don't need reverting to match their hashes.
        # This could probably be done more fool-proof by actually rolling back the files on a transaction fail.
        if bot1 is not None:
            bot1.save()
        if bot2 is not None:
            bot2.save()
        # Save Tags
        bot1_user = participant1.bot.user
        bot2_user = participant2.bot.user
        bot1_tags = parse_tags(result_data.get("bot1_tags"))
        bot2_tags = parse_tags(result_data.get("bot2_tags"))
        # Union tags if both bots belong to the same user
        if bot1_user == bot2_user:
            total_tags = list(set(bot1_tags if bot1_tags else []) | set(bot2_tags if bot2_tags else []))

            if total_tags:
                total_match_tags = []
                for tag in total_tags:
                    tag_obj = Tag.objects.get_or_create(name=tag)
                    total_match_tags.append(MatchTag.objects.get_or_create(tag=tag_obj[0], user=bot1_user)[0])
                # remove tags for this match that belong to this user and were not sent in the form
                match.tags.remove(*match.tags.filter(user=bot1_user).exclude(id__in=[mt.id for mt in total_match_tags]))
                # add everything, this shouldn't cause duplicates
                match.tags.add(*total_match_tags)
        else:
            if bot1_tags:
                p1_match_tags = []
                for tag in bot1_tags:
                    tag_obj = Tag.objects.get_or_create(name=tag)
                    p1_match_tags.append(MatchTag.objects.get_or_create(tag=tag_obj[0], user=bot1_user)[0])
                # remove tags for this match that belong to this user and were not sent in the form
                match.tags.remove(*match.tags.filter(user=bot1_user).exclude(id__in=[mt.id for mt in p1_match_tags]))
                # add everything, this shouldn't cause duplicates
                match.tags.add(*p1_match_tags)

            if bot2_tags:
                p2_match_tags = []
                for tag in bot2_tags:
                    tag_obj = Tag.objects.get_or_create(name=tag)
                    p2_match_tags.append(MatchTag.objects.get_or_create(tag=tag_obj[0], user=bot2_user)[0])
                # remove tags for this match that belong to this user and were not sent in the form
                match.tags.remove(*match.tags.filter(user=bot2_user).exclude(id__in=[mt.id for mt in p2_match_tags]))
                # add everything, this shouldn't cause duplicates
                match.tags.add(*p2_match_tags)
        match.result = result
        match.save()
        # Only do these actions if the match is part of a round
        if result.match.round is not None:
            result.match.round.update_if_completed()

            # Update and record ELO figures
            participant1.starting_elo, participant2.starting_elo = result.get_initial_elos
            result.adjust_elo()

            initial_elo_sum = participant1.starting_elo + participant2.starting_elo

            # Calculate the change in ELO
            # the bot elos have changed so refresh them
            # todo: instead of having to refresh, return data from adjust_elo and apply it here
            sp1, sp2 = result.get_competition_participants
            participant1.resultant_elo = sp1.elo
            participant2.resultant_elo = sp2.elo
            participant1.elo_change = participant1.resultant_elo - participant1.starting_elo
            participant2.elo_change = participant2.resultant_elo - participant2.starting_elo
            participant1.save()
            participant2.save()

            resultant_elo_sum = participant1.resultant_elo + participant2.resultant_elo
            if initial_elo_sum != resultant_elo_sum:
                logger.critical(
                    f"Initial and resultant ELO sum mismatch: "
                    f"Result {result.id}. "
                    f"initial_elo_sum: {initial_elo_sum}. "
                    f"resultant_elo_sum: {resultant_elo_sum}. "
                    f"participant1.elo_change: {participant1.elo_change}. "
                    f"participant2.elo_change: {participant2.elo_change}"
                )

            if config.ENABLE_ELO_SANITY_CHECK:
                if config.DEBUG_LOGGING_ENABLED:
                    logger.info("ENABLE_ELO_SANITY_CHECK enabled. Performing check.")

                # test here to check ELO total and ensure no corruption
                match_competition = result.match.round.competition
                expected_elo_sum = (
                    settings.ELO_START_VALUE
                    * CompetitionParticipation.objects.filter(competition=match_competition).count()
                )
                actual_elo_sum = CompetitionParticipation.objects.filter(competition=match_competition).aggregate(
                    Sum("elo")
                )

                if actual_elo_sum["elo__sum"] != expected_elo_sum:
                    logger.critical(
                        f"ELO SANITY CHECK FAILURE: ELO sum of {actual_elo_sum['elo__sum']} did not match expected value "
                        f"of {expected_elo_sum} upon submission of result {result.id}"
                    )
                elif config.DEBUG_LOGGING_ENABLED:
                    logger.info("ENABLE_ELO_SANITY_CHECK passed!")

            elif config.DEBUG_LOGGING_ENABLED:
                logger.info("ENABLE_ELO_SANITY_CHECK disabled. Skipping check.")

            BotStatistics(sp1).update_stats_based_on_result(result, sp2)
            BotStatistics(sp2).update_stats_based_on_result(result, sp1)

            if result.is_crash_or_timeout:
                try:
                    run_consecutive_crashes_check(result.get_causing_participant_of_crash_or_timeout_result)
                except Exception as e:
                    logger.exception(e)
        return result


def run_consecutive_crashes_check(triggering_participation: MatchParticipation):
    """
    Checks to see whether the last X results for a participant are crashes and, if so, sends an alert.
    :param triggering_participant: The participant who triggered this check and whose bot we should run the check for.
    :return:
    """

    if config.BOT_CONSECUTIVE_CRASH_LIMIT < 1:
        return  # Check is disabled

    if not triggering_participation.bot.competition_participations.filter(active=True).exists():
        return  # No use running the check - bot is already inactive.

    # Get recent match participation records for this bot since its last update
    recent_participations = MatchParticipation.objects.filter(
        bot=triggering_participation.bot, match__result__isnull=False, match__started__gt=F("bot__bot_zip_updated")
    ).order_by("-match__result__created")[: config.BOT_CONSECUTIVE_CRASH_LIMIT]

    # if there's not enough participations yet, then exit without action
    if recent_participations.count() < config.BOT_CONSECUTIVE_CRASH_LIMIT:
        return

    # if any of the previous results weren't a crash or already triggered a crash limit alert, then exit without action
    for recent_participation in recent_participations:
        if not recent_participation.crashed:
            return
        elif recent_participation.triggered_a_crash_limit_alert:
            return

    # Log a crash alert
    BotCrashLimitAlert.objects.create(triggering_match_participation=triggering_participation)

    # If we get to here, all the results were crashes, so take action
    Bots.send_crash_alert(triggering_participation.bot)
