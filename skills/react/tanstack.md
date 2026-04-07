# TanStack Patterns

Type-safe patterns for TanStack Query, Table, and Router.

## TanStack Query

### Typing Queries

Use generics to type your data (and optionally error):

```ts
type User = { id: string; name: string };

const { data, isLoading, error } = useQuery<User>({
  queryKey: ["user", userId],
  queryFn: () => fetchUser(userId),
});
```

Avoid `any` for query data; prefer defining a small interface/type.

### Query Keys

Use **tuple or array keys** with `as const` when constructing them:

```ts
const userQueryKey = (id: string) => ["user", id] as const;
useQuery({ queryKey: userQueryKey(id), queryFn: ... });
```

Don't cast query keys to `as unknown as QueryKey`.

### Mutations

Type mutation functions with meaningful input/output types:

```ts
type UpdateUserInput = { id: string; name: string };
type UpdateUserResult = User;

const mutation = useMutation<UpdateUserResult, Error, UpdateUserInput>({
  mutationFn: (input) => updateUser(input),
});
```

Avoid casting mutation responses; adjust the types or server response instead.

---

## TanStack Table

### Table Data Typing

Always parameterize table hooks and column definitions with your row type:

```ts
type UserRow = {
  id: string;
  name: string;
  email: string;
};

const columns: ColumnDef<UserRow>[] = [
  {
    accessorKey: "name",
    header: "Name",
    cell: (info) => info.getValue(),
  },
];
```

Avoid `ColumnDef<any>` unless absolutely necessary.

### Accessors & Cells

Use proper accessor patterns rather than casts:

```ts
{
  accessorKey: "email",
  cell: (info) => {
    const value = info.getValue<string>();
    return <a href={`mailto:${value}`}>{value}</a>;
  },
}
```

Prefer setting field types on your row type so `info.getValue()` is correctly inferred.

---

## TanStack Router

### Route Params & Search

Define route types so params/search are typed:

```ts
interface UserRouteParams {
  userId: string;
}

interface UserSearch {
  tab?: "overview" | "settings";
}
```

Use router APIs to parse/validate search params instead of casting them.

### Links & Navigation

Avoid casting route params/search to `any` or `unknown` just to satisfy navigation APIs; adjust route config/types instead.
