export default function TextInput({ label, ...props }) {
  return (
    <label className="input-wrap">
      <span>{label}</span>
      <input className="input" {...props} />
    </label>
  );
}
