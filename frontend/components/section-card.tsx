import type { ReactNode } from "react";

type SectionCardProps = {
  title: string;
  eyebrow?: string;
  aside?: ReactNode;
  children: ReactNode;
};

export function SectionCard({ title, eyebrow, aside, children }: SectionCardProps) {
  return (
    <section className="card">
      <div className="card__header">
        <div>
          {eyebrow ? <div className="card__eyebrow">{eyebrow}</div> : null}
          <h2 className="card__title">{title}</h2>
        </div>
        {aside ? <div className="card__aside">{aside}</div> : null}
      </div>
      {children}
    </section>
  );
}
