import Badge from "./Badge";
import Card from "./Card";

export default function StatCard({ title, value, badge, footer }) {
  return (
    <Card>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
        <div>{title}</div>
        {badge ? <Badge>{badge}</Badge> : null}
      </div>
      <h3 style={{ margin: "18px 0 12px", fontSize: "2rem" }}>{value}</h3>
      <p style={{ margin: 0, color: "var(--text-soft)" }}>{footer}</p>
    </Card>
  );
}
