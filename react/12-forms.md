# React Forms -- Controlled, Uncontrolled, Validation, and Libraries

## 1. Controlled Components

A controlled component is a form element whose value is driven entirely by React state. The component renders what React tells it to render, and every change flows through an event handler.

```jsx
function ControlledInput() {
  const [name, setName] = React.useState("");

  return (
    <input
      type="text"
      value={name}
      onChange={(e) => setName(e.target.value)}
    />
  );
}
```

### Why "controlled"?

React is the single source of truth. The DOM input never holds a value that React does not know about. This makes it trivial to:

- Validate on every keystroke.
- Conditionally disable a submit button.
- Transform input (e.g., uppercase, trim).
- Synchronize multiple inputs.

### The `value` + `onChange` contract

| Prop | Purpose |
|------|---------|
| `value` | Tells the input what to display right now |
| `onChange` | Fires on every user interaction; you update state here |

If you supply `value` without `onChange`, React warns and the field becomes **read-only** in practice because the DOM value resets to whatever `value` is on every render.

---

## 2. Uncontrolled Components

An uncontrolled component stores its own state inside the DOM. You read the value imperatively via a `ref`.

```jsx
function UncontrolledInput() {
  const inputRef = React.useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log("Submitted:", inputRef.current.value);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input type="text" defaultValue="hello" ref={inputRef} />
      <button type="submit">Submit</button>
    </form>
  );
}
```

### `defaultValue` vs `value`

| Prop | Behavior |
|------|----------|
| `defaultValue` | Sets initial DOM value; React does NOT control subsequent changes |
| `value` | React owns the value on every render |

`defaultValue` is used once -- during the initial mount. After that the DOM manages the input internally.

---

## 3. Controlled vs Uncontrolled -- Tradeoff Matrix

| Criterion | Controlled | Uncontrolled |
|-----------|-----------|--------------|
| Source of truth | React state | DOM |
| Real-time validation | Easy | Requires imperative reads |
| Performance (large forms) | Re-renders on every keystroke | Minimal re-renders |
| Integration with non-React code | Harder | Easier |
| File inputs | Cannot be controlled (`<input type="file">` is always uncontrolled) | Natural fit |
| Form reset | Reset state manually | `formRef.current.reset()` |
| Debugging | Inspect state | Inspect DOM |

**Rule of thumb:** prefer controlled for most cases. Use uncontrolled when integrating with third-party DOM libraries or when you genuinely need to avoid per-keystroke re-renders (rare in practice with React 18+ batching).

---

## 4. Form Validation Strategies

### 4.1 Validate on `onChange`

```jsx
function OnChangeValidation() {
  const [email, setEmail] = React.useState("");
  const [error, setError] = React.useState("");

  const handleChange = (e) => {
    const val = e.target.value;
    setEmail(val);
    if (val && !val.includes("@")) {
      setError("Must contain @");
    } else {
      setError("");
    }
  };

  return (
    <div>
      <input value={email} onChange={handleChange} />
      {error && <span style={{ color: "red" }}>{error}</span>}
    </div>
  );
}
```

**Pros:** Immediate feedback. **Cons:** Noisy -- user sees errors while still typing.

### 4.2 Validate on `onBlur`

```jsx
function OnBlurValidation() {
  const [email, setEmail] = React.useState("");
  const [error, setError] = React.useState("");

  const validate = () => {
    if (email && !email.includes("@")) {
      setError("Invalid email");
    } else {
      setError("");
    }
  };

  return (
    <input
      value={email}
      onChange={(e) => setEmail(e.target.value)}
      onBlur={validate}
    />
  );
}
```

**Pros:** Less noisy; validates when the user signals they are done with the field. **Cons:** Delayed feedback.

### 4.3 Validate on `onSubmit`

```jsx
function OnSubmitValidation() {
  const [fields, setFields] = React.useState({ name: "", age: "" });
  const [errors, setErrors] = React.useState({});

  const handleSubmit = (e) => {
    e.preventDefault();
    const newErrors = {};
    if (!fields.name) newErrors.name = "Required";
    if (Number(fields.age) < 0) newErrors.age = "Must be positive";
    setErrors(newErrors);
    if (Object.keys(newErrors).length === 0) {
      console.log("Submit", fields);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        value={fields.name}
        onChange={(e) => setFields({ ...fields, name: e.target.value })}
      />
      {errors.name && <span>{errors.name}</span>}
      <input
        value={fields.age}
        onChange={(e) => setFields({ ...fields, age: e.target.value })}
      />
      {errors.age && <span>{errors.age}</span>}
      <button type="submit">Submit</button>
    </form>
  );
}
```

**Best practice in production:** combine onBlur (first touch) + onSubmit (final gate). Show errors on blur, re-validate on submit.

---

## 5. Building a Form from Scratch

```jsx
function RegistrationForm() {
  const [form, setForm] = React.useState({
    username: "",
    email: "",
    password: "",
  });
  const [errors, setErrors] = React.useState({});
  const [submitted, setSubmitted] = React.useState(false);

  const update = (field) => (e) =>
    setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const validate = () => {
    const errs = {};
    if (form.username.length < 3) errs.username = "Min 3 characters";
    if (!/\S+@\S+\.\S+/.test(form.email)) errs.email = "Invalid email";
    if (form.password.length < 8) errs.password = "Min 8 characters";
    return errs;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const errs = validate();
    setErrors(errs);
    if (Object.keys(errs).length === 0) {
      setSubmitted(true);
      // POST to API
    }
  };

  if (submitted) return <p>Registration successful!</p>;

  return (
    <form onSubmit={handleSubmit}>
      {["username", "email", "password"].map((field) => (
        <div key={field}>
          <label>{field}</label>
          <input
            type={field === "password" ? "password" : "text"}
            value={form[field]}
            onChange={update(field)}
          />
          {errors[field] && <span className="error">{errors[field]}</span>}
        </div>
      ))}
      <button type="submit">Register</button>
    </form>
  );
}
```

---

## 6. FormData API

The browser-native `FormData` object extracts all named fields from a `<form>` element. This avoids wiring every input to state.

```jsx
function FormDataExample() {
  const handleSubmit = (e) => {
    e.preventDefault();
    const data = new FormData(e.target);
    const payload = Object.fromEntries(data.entries());
    console.log(payload); // { name: "...", email: "..." }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input name="name" defaultValue="" />
      <input name="email" defaultValue="" />
      <button type="submit">Submit</button>
    </form>
  );
}
```

This pairs well with React 19+ server actions where `FormData` is the primary transport.

### Pitfall: multiple values for the same name

Checkboxes or `<select multiple>` can produce duplicate keys. Use `data.getAll("colors")` instead of `data.get("colors")`.

---

## 7. File Uploads

`<input type="file">` is always uncontrolled -- you cannot set its `value` programmatically (security restriction).

```jsx
function FileUpload() {
  const [preview, setPreview] = React.useState(null);

  const handleFile = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = () => setPreview(reader.result);
      reader.readAsDataURL(file);
    }
  };

  return (
    <div>
      <input type="file" accept="image/*" onChange={handleFile} />
      {preview && <img src={preview} alt="preview" width={200} />}
    </div>
  );
}
```

To send to a server, build `FormData` and use `fetch` with no `Content-Type` header (the browser sets `multipart/form-data` automatically).

---

## 8. Dynamic Form Fields

```jsx
function DynamicFields() {
  const [fields, setFields] = React.useState([{ id: 1, value: "" }]);

  const addField = () =>
    setFields([...fields, { id: Date.now(), value: "" }]);

  const removeField = (id) =>
    setFields(fields.filter((f) => f.id !== id));

  const updateField = (id, val) =>
    setFields(fields.map((f) => (f.id === id ? { ...f, value: val } : f)));

  return (
    <div>
      {fields.map((f) => (
        <div key={f.id}>
          <input
            value={f.value}
            onChange={(e) => updateField(f.id, e.target.value)}
          />
          <button onClick={() => removeField(f.id)}>X</button>
        </div>
      ))}
      <button onClick={addField}>Add field</button>
    </div>
  );
}
```

**Key pitfall:** never use array index as `key` when items can be reordered or removed. Use a stable identifier.

---

## 9. Debounced Validation

Useful for async validation (e.g., checking if a username is taken).

```jsx
function useDebouncedValue(value, delay) {
  const [debounced, setDebounced] = React.useState(value);
  React.useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return debounced;
}

function UsernameField() {
  const [username, setUsername] = React.useState("");
  const debouncedUsername = useDebouncedValue(username, 500);
  const [available, setAvailable] = React.useState(null);

  React.useEffect(() => {
    if (!debouncedUsername) return;
    // Simulate API call
    fetch(`/api/check-username?u=${debouncedUsername}`)
      .then((r) => r.json())
      .then((data) => setAvailable(data.available));
  }, [debouncedUsername]);

  return (
    <div>
      <input value={username} onChange={(e) => setUsername(e.target.value)} />
      {available === true && <span>Available</span>}
      {available === false && <span>Taken</span>}
    </div>
  );
}
```

---

## 10. React Hook Form vs Formik

| Feature | React Hook Form | Formik |
|---------|----------------|--------|
| Re-renders | Minimal (uncontrolled under the hood) | Re-renders on every field change by default |
| Bundle size | ~9 KB | ~15 KB |
| API style | `register` / `useForm` hooks | `<Formik>` render prop or `useFormik` |
| Validation | Integrates with Yup, Zod, Joi via resolvers | Built-in `validate` prop or Yup via `validationSchema` |
| Performance at scale | Excellent for large forms | Can degrade without careful optimization |
| Learning curve | Lower (hook-centric) | Moderate (more concepts: Field, FieldArray, etc.) |

### React Hook Form example

```jsx
import { useForm } from "react-hook-form";

function RHFExample() {
  const { register, handleSubmit, formState: { errors } } = useForm();

  const onSubmit = (data) => console.log(data);

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register("email", { required: "Email is required" })} />
      {errors.email && <span>{errors.email.message}</span>}
      <button type="submit">Submit</button>
    </form>
  );
}
```

### Formik example

```jsx
import { Formik, Field, Form, ErrorMessage } from "formik";
import * as Yup from "yup";

function FormikExample() {
  return (
    <Formik
      initialValues={{ email: "" }}
      validationSchema={Yup.object({
        email: Yup.string().email("Invalid").required("Required"),
      })}
      onSubmit={(values) => console.log(values)}
    >
      <Form>
        <Field name="email" type="email" />
        <ErrorMessage name="email" component="span" />
        <button type="submit">Submit</button>
      </Form>
    </Formik>
  );
}
```

---

## 11. Common Pitfalls

1. **Setting `value` without `onChange`** -- the input becomes effectively read-only. React warns in the console.
2. **Using `defaultValue` and `value` together** -- React ignores `defaultValue` when `value` is present. No error, but confusing.
3. **Forgetting `name` attributes** -- `FormData` relies on `name` to build key-value pairs.
4. **Calling `e.target.value` inside `setState` callback asynchronously** -- the synthetic event may be pooled/nullified (React 16). In React 17+, events are not pooled, so this is safe.
5. **Not calling `e.preventDefault()`** on form submit -- the page reloads.

---

## 12. Output-Based Interview Questions

### Question 1: Input without onChange handler -- what happens?

```jsx
function App() {
  const [val] = React.useState("locked");
  return <input value={val} />;
}
```

**What renders? Can the user type?**

**Answer:**
The input displays "locked". The user **cannot** change the text. Every keystroke is immediately overwritten because React re-renders with `value="locked"` and no `onChange` ever updates state. React also logs a console warning: _"You provided a `value` prop to a form field without an `onChange` handler."_

---

### Question 2: defaultValue vs value -- behavior difference?

```jsx
function App() {
  const [show, setShow] = React.useState(true);

  return (
    <div>
      {show && (
        <>
          <input id="a" defaultValue="initial" />
          <input id="b" value="initial" onChange={() => {}} />
        </>
      )}
      <button onClick={() => setShow(false)}>Unmount</button>
      <button onClick={() => setShow(true)}>Remount</button>
    </div>
  );
}
```

**User types "hello" into input A, then clicks Unmount then Remount. What does each input show?**

**Answer:**
After remount, **both** inputs show `"initial"`. Input A was uncontrolled but the component unmounted and remounted, creating a fresh DOM node with `defaultValue="initial"`. Input B always shows `"initial"` because it is controlled. The key difference is visible **before** unmount: typing into A changes its display (DOM-managed), typing into B does nothing visible (the `onChange` does not update state).

---

### Question 3: State update inside onChange -- how many renders?

```jsx
function App() {
  const [first, setFirst] = React.useState("");
  const [last, setLast] = React.useState("");
  console.log("render");

  const handleChange = (e) => {
    setFirst(e.target.value);
    setLast(e.target.value.toUpperCase());
  };

  return <input value={first} onChange={handleChange} />;
}
```

**User types "a". How many times does "render" print (after the initial render)?**

**Answer:**
**Once.** React 18 batches both `setFirst` and `setLast` into a single re-render, even inside event handlers. In React 17 and earlier, event handler state updates were already batched, so the answer is the same. You would only see two renders if the updates were inside a `setTimeout` or `Promise` callback **in React 17** (React 18 batches those too).

---

### Question 4: FormData with checkbox

```jsx
function App() {
  const handleSubmit = (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    console.log("agree:", fd.get("agree"));
  };

  return (
    <form onSubmit={handleSubmit}>
      <input type="checkbox" name="agree" value="yes" />
      <button type="submit">Submit</button>
    </form>
  );
}
```

**User submits without checking the checkbox. What is logged?**

**Answer:**
`agree: null`. Unchecked checkboxes are **not included** in `FormData` at all. `fd.get("agree")` returns `null`. This is a common gotcha -- you must handle the absence of the key, not look for `false`.

---

### Question 5: Controlled textarea

```jsx
function App() {
  return <textarea value="fixed text" />;
}
```

**Can the user edit the textarea?**

**Answer:**
No. Just like `<input>`, a `<textarea>` with `value` and no `onChange` is read-only. React warns in the console. To make it editable, either add an `onChange` that updates state, or use `defaultValue` instead.

---

## 13. Summary

- **Controlled** = React state drives the input. Use for most forms.
- **Uncontrolled** = DOM drives the input. Use for file inputs, third-party integrations, or performance-sensitive cases.
- **Validation timing** matters for UX: onBlur for first touch, onSubmit as final gate.
- **FormData API** is lightweight and pairs naturally with uncontrolled forms and server actions.
- **React Hook Form** is the current community favorite for performance and DX.
- Always call `e.preventDefault()` on form submit, use stable keys for dynamic fields, and never set `value` without `onChange`.
