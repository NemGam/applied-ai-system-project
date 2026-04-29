type PreferenceInputProps = {
    label?: string;
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
    type?: 'text' | 'number';
    min?: string;
    max?: string;
    step?: string;
    multiline?: boolean;
    rows?: number;
};

export default function PreferenceInput({
    label,
    value,
    onChange,
    placeholder,
    type = 'text',
    min,
    max,
    step,
    multiline = false,
    rows = 4,
}: PreferenceInputProps) {
    return (
        <label>
            {label}
            {multiline ? (
                <textarea
                    value={value}
                    onChange={(event) => onChange(event.target.value)}
                    placeholder={placeholder}
                    rows={rows}
                />
            ) : (
                <input
                    type={type}
                    value={value}
                    onChange={(event) => onChange(event.target.value)}
                    placeholder={placeholder}
                    min={min}
                    max={max}
                    step={step}
                />
            )}
        </label>
    );
}
