"use client";

import {
  type MouseEvent,
  type ReactNode,
  useEffect,
  useId,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { createPortal } from "react-dom";

type ActionMenuProps = {
  label: string;
  children: ReactNode;
  menuClassName?: string;
};

type MenuPosition = {
  left: number;
  top: number;
};

const VIEWPORT_GAP = 8;
const MENU_GAP = 8;

export default function ActionMenu({
  label,
  children,
  menuClassName = "w-44",
}: ActionMenuProps) {
  const menuId = useId();
  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [position, setPosition] = useState<MenuPosition | null>(null);

  useLayoutEffect(() => {
    if (!isOpen || triggerRef.current === null || menuRef.current === null) {
      return;
    }

    const triggerBounds = triggerRef.current.getBoundingClientRect();
    const menuBounds = menuRef.current.getBoundingClientRect();
    const left = Math.min(
      window.innerWidth - menuBounds.width - VIEWPORT_GAP,
      Math.max(VIEWPORT_GAP, triggerBounds.right - menuBounds.width),
    );
    const spaceBelow = window.innerHeight - triggerBounds.bottom;
    const top =
      spaceBelow >= menuBounds.height + MENU_GAP + VIEWPORT_GAP
        ? triggerBounds.bottom + MENU_GAP
        : Math.max(
            VIEWPORT_GAP,
            triggerBounds.top - menuBounds.height - MENU_GAP,
          );

    setPosition({ left, top });
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;

    function closeOnOutsideClick(event: PointerEvent) {
      const target = event.target;
      if (!(target instanceof Node)) return;

      if (
        triggerRef.current?.contains(target) ||
        menuRef.current?.contains(target)
      ) {
        return;
      }

      setIsOpen(false);
    }

    function closeOnEscape(event: KeyboardEvent) {
      if (event.key !== "Escape") return;

      setIsOpen(false);
      triggerRef.current?.focus();
    }

    function closeOnViewportChange() {
      setIsOpen(false);
    }

    document.addEventListener("pointerdown", closeOnOutsideClick);
    document.addEventListener("keydown", closeOnEscape);
    window.addEventListener("resize", closeOnViewportChange);
    window.addEventListener("scroll", closeOnViewportChange, true);

    return () => {
      document.removeEventListener("pointerdown", closeOnOutsideClick);
      document.removeEventListener("keydown", closeOnEscape);
      window.removeEventListener("resize", closeOnViewportChange);
      window.removeEventListener("scroll", closeOnViewportChange, true);
    };
  }, [isOpen]);

  function toggleMenu() {
    setIsOpen((currentValue) => !currentValue);
    setPosition(null);
  }

  function closeAfterAction(event: MouseEvent<HTMLDivElement>) {
    const target = event.target;
    if (!(target instanceof Element)) return;

    if (target.closest("a, button")) {
      setIsOpen(false);
    }
  }

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        aria-label={label}
        aria-haspopup="menu"
        aria-expanded={isOpen}
        aria-controls={isOpen ? menuId : undefined}
        onClick={toggleMenu}
        className="flex size-8 cursor-pointer select-none items-center justify-center rounded-lg text-slate-500 caret-transparent transition hover:bg-slate-100 hover:text-slate-900 focus-visible:outline-2 focus-visible:outline-blue-600"
      >
        <svg
          aria-hidden="true"
          viewBox="0 0 24 24"
          fill="currentColor"
          className="size-5"
        >
          <circle cx="5" cy="12" r="1.75" />
          <circle cx="12" cy="12" r="1.75" />
          <circle cx="19" cy="12" r="1.75" />
        </svg>
      </button>

      {isOpen &&
        createPortal(
          <div
            ref={menuRef}
            id={menuId}
            role="menu"
            aria-label={label}
            onClick={closeAfterAction}
            style={
              position === null
                ? { left: 0, top: 0, visibility: "hidden" }
                : { left: position.left, top: position.top }
            }
            className={`fixed z-[100] overflow-hidden rounded-lg border border-slate-200 bg-white py-1 text-left shadow-lg ${menuClassName}`}
          >
            {children}
          </div>,
          document.body,
        )}
    </>
  );
}
