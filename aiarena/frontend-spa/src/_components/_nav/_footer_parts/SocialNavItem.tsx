import React from "react";
import FooterNavItem from "./FooterNavItem";
import { FooterLink } from "@/_data/footerLinks";
import WrappedTitle from "@/_components/_display/WrappedTitle";
// import WrappedTitle from "@/_components/_display/WrappedTitle";

interface SocialComponentProps {
  links: FooterLink[];
}

const SocialComponent: React.FC<SocialComponentProps> = ({ links }) => {
  return (
    <div className="mb-16 px-8 text-center flex-1 mx-auto  w-full">
      <WrappedTitle title="Communities" />
      <ul className="space-y-2 flex flex-col items-center">
        {links.map((link) => (
          <FooterNavItem
            key={link.href}
            href={link.href}
            name={link.name}
            icon={link.icon}
            invertIcon={link.invertIcon}
          />
        ))}
      </ul>
    </div>
  );
};

export default SocialComponent;
