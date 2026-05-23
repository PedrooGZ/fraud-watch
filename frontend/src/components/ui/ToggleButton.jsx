export default function ToggleButton({ active, onClick, children, disabled = false }) {
  return (
    <button
      className={`btn ${active ? "" : "ghost"}`.trim()}
      onClick={onClick}
      type="button"
      disabled={disabled}
    >
      {children}
    </button>
  );
}
