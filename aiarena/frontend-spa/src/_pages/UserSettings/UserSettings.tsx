import { graphql, useLazyLoadQuery } from "react-relay";

import UserSettingsSection from "@/_components/_sections/UserSettingsSection";
import { UserSettingsQuery } from "./__generated__/UserSettingsQuery.graphql";

export default function UserSettings() {
  const data = useLazyLoadQuery<UserSettingsQuery>(
    graphql`
      query UserSettingsQuery {
        viewer {
          ...UserSettingsSection_viewer
        }
      }
    `,
    {}
  );

  if (!data.viewer) {
    window.location.replace("/accounts/login");
    return null;
  }

  return (
    <>
      <UserSettingsSection viewer={data.viewer} />
    </>
  );
}
