# Formik Patterns

Type-safe patterns for Formik form handling.

## useField

Prefer **`helpers.setValue` / `setTouched`** instead of calling `field.onChange` with fake events.

Do **not** construct fake `React.ChangeEvent` just to satisfy `onChange` types:

```ts
// BAD - don't do this
const event = {
  target: { name, value, checked },
} as unknown as React.ChangeEvent<HTMLInputElement>;
field.onChange(event);

// GOOD - use helpers directly
helpers.setValue(checked);
```

### Preferred Pattern

```ts
type ToggleSwitchFieldProps = Omit<
  React.ComponentProps<typeof ToggleSwitch>,
  "checked" | "defaultChecked" | "onChange"
> & {
  name: string;
  onChange?: (checked: boolean) => void;
};

function ToggleSwitchField({ name, onChange, ...rest }: ToggleSwitchFieldProps) {
  const [{ value }, , helpers] = useField<boolean>({ name, type: "checkbox" });

  const handleChange = (checked: boolean) => {
    helpers.setValue(checked);   // updates Formik
    onChange?.(checked);         // optional side-effects
  };

  return (
    <ToggleSwitch
      {...rest}
      checked={!!value}
      onChange={handleChange}
    />
  );
}
```

## Field Component

If using `<Field component={...} />`:

- Prefer a prop signature that receives `field` and `form` explicitly
- Use `field.value`, `field.onChange`, etc. directly, no casts

```ts
type CustomFieldProps = FieldProps & {
  label?: string;
};

function CustomTextField({ field, form, label, ...rest }: CustomFieldProps) {
  return <input {...field} {...rest} />;
}
```

Don't re-export `FieldProps["field"]` into your public component API unless you truly need to.
