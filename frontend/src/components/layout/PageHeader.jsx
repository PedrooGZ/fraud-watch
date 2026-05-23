import Badge from "../ui/Badge";
import Button from "../ui/Button";

export default function PageHeader({ title, subtitle, badge, actionLabel, onAction, actionDisabled = false }) {
  return (
    <header className="page-header">
      <div className="page-header-top">
        <div><h1>{title}</h1><p>{subtitle}</p></div>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          {badge ? <Badge>{badge}</Badge> : null}
          {actionLabel ? <Button variant="primary" onClick={onAction} disabled={actionDisabled}>{actionLabel}</Button> : null}
        </div>
      </div>
    </header>
  );
}
