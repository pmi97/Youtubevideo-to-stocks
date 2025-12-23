import { SelectHTMLAttributes, forwardRef } from 'react';

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
    label?: string;
    icon?: string;
    options: { value: string; label: string }[];
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
    ({ label, icon, options, className = '', ...props }, ref) => {
        return (
            <div className="space-y-2">
                {label && (
                    <label className="flex items-center gap-2 text-sm font-medium text-white/90">
                        {icon && <span>{icon}</span>}
                        {label}
                    </label>
                )}
                <select
                    ref={ref}
                    className={`input-base cursor-pointer ${className}`}
                    {...props}
                >
                    {options.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                            {opt.label}
                        </option>
                    ))}
                </select>
            </div>
        );
    }
);

Select.displayName = 'Select';
