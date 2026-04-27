type GenreSelectProps = {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
  formatOptionLabel?: (option: string) => string;
};

export default function GenreSelect({
  label,
  value,
  options,
  onChange,
  formatOptionLabel,
}: GenreSelectProps) {
  return (
    <label>
      {label}
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">Any genre</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {formatOptionLabel ? formatOptionLabel(option) : option}
          </option>
        ))}
      </select>
    </label>
  );
}
