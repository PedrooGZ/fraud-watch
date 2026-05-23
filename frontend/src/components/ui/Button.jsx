export default function Button({ children, variant = "default", block = false, className = "", ...props }) {
  const classes = ["btn", variant === "primary" ? "primary" : "", block ? "block" : "", className]
    .filter(Boolean)
    .join(" ");
  return <button className={classes} {...props}>{children}</button>;
}
