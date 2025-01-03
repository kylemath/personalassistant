# Todo Widget Planning Meeting

**Participants:**

- Sarah (Senior Engineer)
- Alex (Junior Engineer)
- Maya (Intern)
- Tom (Engineering Supervisor)

**Tom**: Let's discuss the implementation of our new hierarchical todo widget. Sarah, could you start by outlining the key requirements?

**Sarah**: Based on the requirements, we need:

1. A hierarchical todo system with 3 nesting levels
2. Visual consistency with existing Calendar and Email widgets
3. Zoom-in functionality that focuses on the current level
4. Context preservation while navigating the hierarchy

Here's a rough component structure:

```typescript
interface TodoItem {
  id: string;
  title: string;
  completed: boolean;
  children?: TodoItem[];
  parentId?: string;
  level: number; // 1, 2, or 3
  createdAt: number;
  updatedAt: number;
}

interface TodoState {
  items: TodoItem[];
  currentPath: string[]; // Array of IDs representing current navigation
  loading: boolean;
  error: string | null;
}
```

**Maya**: I have a question about the UI. How should we handle the transition between levels?

**Alex**: I think we could use a sliding animation, similar to how mobile apps handle hierarchical navigation. When you click a todo item, its children slide in from the right, and the parent list slides out to the left.

**Sarah**: Good thinking, Alex. We should also maintain a breadcrumb trail at the top. Here's a basic layout structure:

```typescript
const TodoWidget: React.FC = () => {
  return (
    <div className="widget todo-widget">
      <div className="widget-header">
        <h2>📝 Tasks</h2>
        <div className="widget-actions">
          <button className="widget-button">Add Task</button>
        </div>
      </div>
      <div className="todo-breadcrumbs">{/* Navigation breadcrumbs */}</div>
      <div className="widget-content">
        <div className="todo-list">{/* Animated todo lists */}</div>
      </div>
    </div>
  );
};
```

**Tom**: What about the state management? We'll need to integrate this with our existing Redux store.

**Sarah**: Here's a proposed Redux slice structure:

```typescript
// todoSlice.ts
interface TodoSliceState {
  todos: {
    [id: string]: TodoItem;
  };
  navigation: {
    currentPath: string[];
    previousPath: string[];
  };
  ui: {
    loading: boolean;
    error: string | null;
    animatingDirection: "left" | "right" | null;
  };
}

const todoSlice = createSlice({
  name: "todos",
  initialState,
  reducers: {
    addTodo: (state, action: PayloadAction<TodoItem>) => {
      state.todos[action.payload.id] = action.payload;
    },
    navigateToLevel: (state, action: PayloadAction<string[]>) => {
      state.navigation.previousPath = state.navigation.currentPath;
      state.navigation.currentPath = action.payload;
    },
    // ... other reducers
  },
});
```

**Maya**: How should we handle the animations when transitioning between levels?

**Sarah**: Good question. Let's use CSS transitions with React's `CSSTransition` component:

```css
.todo-list-container {
  position: relative;
  overflow: hidden;
}

.todo-list {
  position: absolute;
  width: 100%;
  transition: transform 0.3s ease-in-out;
}

.todo-list-enter {
  transform: translateX(100%);
}

.todo-list-enter-active {
  transform: translateX(0);
}

.todo-list-exit {
  transform: translateX(0);
}

.todo-list-exit-active {
  transform: translateX(-100%);
}
```

**Alex**: Should we implement drag-and-drop for reordering tasks?

**Tom**: Let's keep that as a future enhancement. For MVP, we should focus on:

1. Basic CRUD operations for todos
2. Smooth level navigation
3. Visual hierarchy indication
4. Proper state management

**Sarah**: Agreed. Here's how we could structure the todo item component:

```typescript
interface TodoItemProps {
  todo: TodoItem;
  level: number;
  onNavigate: (todoId: string) => void;
}

const TodoItem: React.FC<TodoItemProps> = ({ todo, level, onNavigate }) => {
  return (
    <div className={`todo-item level-${level}`}>
      <div className="todo-content">
        <input
          type="checkbox"
          checked={todo.completed}
          onChange={() => handleToggleComplete(todo.id)}
        />
        <span className="todo-title">{todo.title}</span>
        {todo.children && todo.children.length > 0 && (
          <button className="todo-expand" onClick={() => onNavigate(todo.id)}>
            <span className="todo-count">{todo.children.length}</span>
            <svg>{/* Chevron right icon */}</svg>
          </button>
        )}
      </div>
    </div>
  );
};
```

**Maya**: How should we handle the breadcrumb navigation?

**Sarah**: Let's implement it like this:

```typescript
const TodoBreadcrumbs: React.FC = () => {
  const path = useSelector(
    (state: RootState) => state.todos.navigation.currentPath
  );
  const todos = useSelector((state: RootState) => state.todos.todos);

  return (
    <div className="todo-breadcrumbs">
      <button onClick={() => navigateToRoot()}>All Tasks</button>
      {path.map((todoId, index) => (
        <React.Fragment key={todoId}>
          <span className="breadcrumb-separator">›</span>
          <button onClick={() => navigateToLevel(path.slice(0, index + 1))}>
            {todos[todoId].title}
          </button>
        </React.Fragment>
      ))}
    </div>
  );
};
```

**Tom**: Let's outline the implementation phases:

### Phase 1: Basic Structure (Maya)

- Set up TodoWidget component
- Implement basic todo list rendering
- Add "Add Task" functionality

### Phase 2: State Management (Alex)

- Implement Redux slice
- Add CRUD operations
- Set up navigation state

### Phase 3: Hierarchy & Navigation (Sarah)

- Implement level navigation
- Add breadcrumb trail
- Handle animations

### Phase 4: Polish & Integration (Team)

- Style matching with other widgets
- Error handling
- Loading states
- Performance optimization

**Sarah**: Maya, you can start with the basic component structure. Alex, you can work on the Redux implementation. I'll help with the navigation and animation logic.

**Maya**: Got it! Should I create a PR with the basic component structure first?

**Tom**: Yes, that would be great. Let's aim to have the basic structure ready by tomorrow, then we can iterate on the functionality.

**Sarah**: Remember to follow our existing widget patterns:

- Use the same header structure
- Match the padding and spacing
- Use consistent button styles
- Implement loading and error states

**Alex**: Should we add a toggle for showing/hiding completed tasks?

**Sarah**: Good idea! We can add it to the header actions, similar to the email widget's category toggles:

```typescript
<div className="todo-toggles">
  <button
    className={`todo-toggle ${showCompleted ? "active" : ""}`}
    onClick={() => setShowCompleted(!showCompleted)}
  >
    ✓ Completed
  </button>
</div>
```

**Tom**: Excellent planning, team. Let's reconvene tomorrow to review progress and address any challenges. Maya, feel free to ask Sarah or Alex if you need any help with the initial implementation.

**Maya**: Thanks! I'll start working on the basic structure right away.

**Tom**: Great! Let's wrap up here and get started. Remember to maintain type safety and add tests as we go.
