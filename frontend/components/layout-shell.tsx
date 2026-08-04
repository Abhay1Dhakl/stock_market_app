import type { ReactNode } from "react";
import Link from "next/link";

type LayoutShellProps = {
  title: string;
  description: string;
  children: ReactNode;
};

const navItems = [
  { href: "/", label: "Home" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/review", label: "Review" },
  { href: "/admin", label: "Admin" },
  { href: "/login", label: "Login" },
];

export function LayoutShell({ title, description, children }: LayoutShellProps) {
  return (
    <main>
      <div className="shell">
        <header className="shell__header">
          <div>
            <div className="shell__eyebrow">Stock Market Intelligence</div>
            <h1 className="shell__title">{title}</h1>
            <p className="shell__description">{description}</p>
          </div>
          <nav className="shell__nav" aria-label="Primary">
            {navItems.map((item) => (
              <Link key={item.href} href={item.href}>
                {item.label}
              </Link>
            ))}
          </nav>
        </header>
        {children}
      </div>
    </main>
  );
}
