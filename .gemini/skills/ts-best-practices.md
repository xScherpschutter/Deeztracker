---
name: ts-best-practices
description: Core principles for advanced TypeScript engineering, type safety, and Vue 3 integrations.
---
# Skill: TypeScript Advanced Engineering

## Core Principle
Prioritize Type Safety, Readability, and Maintainability. Code must be "Self-Documenting" through strict typing and exhaustive definitions.

## 1. Type Definitions & Interfaces
- **Strict Typing:** Never use `any`. Use `unknown` if a type is truly uncertain, followed by a type guard.
- **Naming Convention:** Use PascalCase for `Interfaces` and `Types`. Prefixing with "I" (e.g., IUser) is discouraged; use clear, descriptive names instead.
- **Deezer API Models:** Create dedicated interfaces for all API responses (e.g., `Track`, `Album`, `Artist`). 
- **Domain Mapping:** Transform raw API data into internal "Domain Models" using a mapping layer to decouple the UI from external API changes.

## 2. Advanced Type Patterns
- **Discriminated Unions:** Use them for handling UI states (e.g., `type AsyncState = { status: 'loading' } | { status: 'success', data: T } | { status: 'error', error: Error }`).
- **Utility Types:** Leverage `Pick`, `Omit`, `Partial`, and `Readonly` to avoid code duplication and ensure immutability where applicable.
- **Enums vs. Const Objects:** Prefer `as const` objects or String Unions over Enums for better tree-shaking and runtime performance in the frontend.

## 3. Component & Composable Typing (Vue 3)
- **Props & Emits:** Always use `defineProps<{ ... }>()` and `defineEmits<{ ... }>()` for full IDE support and compile-time checks.
- **Refs:** Explicitly type refs when the initial value is null or complex: `const track = ref<Track | null>(null)`.
- **Template Refs:** Use `ref<HTMLDivElement | null>(null)` for DOM elements to ensure safety during manipulation.

## 4. Anti-Patterns to Avoid
- **Implicit Any:** Ensure `noImplicitAny` is true in `tsconfig.json`.
- **Type Assertions:** Avoid `as Type` (casting) unless strictly necessary for external libraries. Use Type Guards (`is` operator) instead.
- **Non-null Assertions:** Avoid `!`. Use optional chaining `?.` or explicit null checks to prevent runtime crashes.
- **Logic in Interfaces:** Interfaces must only describe data shapes, never implementation logic.

## 5. Error Handling & Safety
- **Try-Catch Typing:** Always handle the `error` in catch blocks as `Error` or a custom error type using a check: `if (error instanceof Error)`.
- **Zod/Valibot Integration:** (Recommended) Use a validation library to parse and validate Deezer API responses at the network boundary to ensure they match expected TypeScript interfaces.