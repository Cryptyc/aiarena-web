import { useState, useEffect } from "react";
// import NavItem from "./_nav_parts/NavItem";
// import MobileNavItem from "./_nav_parts/MobileNavItem";
// import AuthNavBar from "./_nav_parts/AuthNavbar";
import { getPublicPrefix } from "@/_lib/getPublicPrefix";
import { Link, NavLink } from "react-router";

const navLinks = [
  {
    title: "Home",
    path: `${getPublicPrefix()}/`,
    showLoggedIn: true,
    showLoggedOut: true,
    featureFlag: null,
  },
  {
    title: "Wiki",
    path: "https://aiarena.net/wiki/",
    showLoggedIn: true,
    showLoggedOut: true,
    featureFlag: null,
  },
  {
    title: "About us",
    path: `${getPublicPrefix()}/about/`,
    showLoggedIn: true,
    showLoggedOut: true,
    featureFlag: null,
  },
  {
    title: "Profile",
    path: `${getPublicPrefix()}/profile/`,
    showLoggedIn: true,
    showLoggedOut: false,
    featureFlag: null,
  },
];

const navbarTitle = {
  title: "AI Arena",
};

function Navbar() {
  const [navbar, setNavbar] = useState(false);
  // const router = usePathname();
  // const { viewer } = useViewerContext();

  const handleMenu = () => {
    if (navbar === true) {
      setNavbar(!navbar);
      document.body.style.overflow = "unset";
    } else {
      setNavbar(!navbar);
      document.body.style.overflow = "hidden";
    }
  };

  const handleWindowResize = () => {
    if (window.innerWidth >= 760) {
      // Only close the navbar on larger screens
      setNavbar(false);
      document.body.style.overflow = "unset";
    }
  };

  // const handleMobileNavItemClick = () => {
  //   setNavbar(false);
  //   document.body.style.overflow = "unset";
  // };

  useEffect(() => {
    // Add event listener when the component mounts
    window.addEventListener("resize", handleWindowResize);

    // Clean up the event listener when the component unmounts
    return () => {
      window.removeEventListener("resize", handleWindowResize);
    };
  }, []);

  return (
    <>
      <nav className="w-full bg-neutral-900 px-2 text-white dark:bg-gray-900 font-sans sticky top-0 z-50">
        <div className="flex justify-between md:p-3 md:flex ">
          <Link
            to={navLinks[0].path}
            className="flex justify-between items-center"
          >
            <img
              className="pr-2 invert"
              src={`${getPublicPrefix()}/assets_logo/ai-arena-logo.svg`}
              alt="AI-arena-logo"
              width={48}
              height={48}
            />
            <h2 className="text-2xl font-bold md:5pl:5 py-4 md:py-0 pb-5">
              {navbarTitle.title}
            </h2>
          </Link>

          {/* Phone */}
          <div className="md:hidden py-4">
            <button
              className="py-3 rounded-md pr-4"
              onClick={() => handleMenu()}
            >
              <p>IMG</p>
              {/* {navbar ? (
                <div>
                  <Image
                    src={`${getPublicPrefix()}/icons/cross.svg`}
                    width={24}
                    height={24}
                    alt="Close menu"
                    className="invert w-6 h-6"
                  />
                </div>
              ) : (
                <Image
                  src={`${getPublicPrefix()}/icons/menu.svg`}
                  width={24}
                  height={24}
                  alt="menu"
                  className="invert w-6 h-6"
                />
              )} */}
            </button>
          </div>
          {/* pc nav */}
          <div className="ml-40 hidden md:flex justify-between">
            {/* Container for Nav Items */}
            <div className="flex flex-col">
              <ul className="flex flex-wrap">
                {navLinks.map((link, index) => (
                  <li key={index} className={`pb-2`}>
                    <NavLink
                      to={link.path}
                      // onClick={handleWindowResize}
                      className={({ isActive }) =>
                        isActive ? "border-b-2 border-customGreen" : ""
                      }
                    >
                      {link.title}
                    </NavLink>

                    {/* We used to use NavItem for this item */}
                  </li>
                ))}
              </ul>
            </div>

            {/* Auth NavBar stays top-right */}
            {/* <div className="ml-auto">
              <AuthNavBar />
            </div> */}
          </div>
        </div>
        {/* {navbar === true ? (
          <div className={`md:block ${navbar ? "block" : "hidden"}`}>
            <ul className="md:h-auto md:flex mt-8 h-screen max-h-[calc(100vh-7rem)] overflow-y-auto">
              {navLinks.map((link, index) => (
                <li
                  key={index}
                  className={`${
                    router === `${link.path}`
                      ? "border-b-2 border-t-2 border-customGreen"
                      : ""
                  }`}
                >
                  <MobileNavItem
                    key={index}
                    href={link.path}
                    onClick={handleMobileNavItemClick}
                    className={
                      router === `${link.path}`
                        ? "border-b-2 border-t-2 border-customGreen"
                        : ""
                    }
                  >
                    {link.title}
                  </MobileNavItem>
                </li>
              ))}

              <li className="flex justify-center pb-10">
                <AuthNavBar />
              </li>
            </ul>
          </div>
        ) : null} */}
      </nav>
    </>
  );
}

export default Navbar;
