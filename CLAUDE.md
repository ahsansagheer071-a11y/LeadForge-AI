# CLAUDE.md

# LeadForge AI

This file is the permanent brain of LeadForge AI.

Always read this file before starting any task.

Never ignore these instructions.

---

# Project Overview

LeadForge AI is a premium AI-powered Lead Intelligence SaaS.

Purpose:

- Discover local businesses
- Analyze websites using AI
- Generate screenshots
- Score leads
- Generate AI outreach
- Manage leads through a CRM
- Provide business analytics

This is an enterprise SaaS.

Everything built must feel premium.

---

# Tech Stack

Backend

- FastAPI
- PostgreSQL
- SQLAlchemy 2
- Alembic
- JWT Authentication
- Google Gemini
- SerpAPI
- Cloudinary
- Playwright

Frontend

- React
- TypeScript
- Vite
- React Query
- React Router
- Lucide Icons
- CSS Modules + Global Styles

---

# Project Goal

Every screen should look like a modern SaaS such as:

- HubSpot
- Apollo
- Clay
- Notion
- Linear
- Stripe Dashboard

Never build beginner-level interfaces.

---

# Architecture

Backend

Routes
↓

Services
↓

Repositories
↓

Database

Business logic belongs inside Services.

Routes must remain thin.

Repositories only handle database queries.

Never mix responsibilities.

---

Frontend

Pages

↓

Reusable Components

↓

Hooks

↓

API Layer

↓

Backend

Never place business logic inside UI components.

Keep components reusable.

---

# Folder Rules

Frontend

pages/

Complete screens.

components/

Reusable UI only.

hooks/

React hooks only.

services/

API calls only.

styles/

Global design system.

Backend

api/

Endpoints only.

services/

Business logic.

repositories/

Database queries.

models/

ORM models.

schemas/

Pydantic.

---

# API Rules

Never hardcode URLs.

Always use existing API services.

Never duplicate API logic.

Reuse existing endpoints whenever possible.

If backend already supports something,

DO NOT create another endpoint.

---

# Database Rules

Never duplicate tables.

Never duplicate relationships.

Always create Alembic migrations.

Never directly modify production schema.

---

# General Rules

Before writing code:

Understand existing implementation.

Reuse existing components.

Respect current architecture.

Avoid unnecessary refactoring.

Never rewrite working code.

Improve only what is required.

---

# Design Philosophy

LeadForge AI must always feel premium.

The UI should look clean, modern, spacious, and enterprise-ready.

Prioritize clarity over decoration.

Every screen should look production-ready.

Never build student-level interfaces.

---

# Design System

Every page must follow the same visual language.

Use:

- Consistent spacing
- Consistent typography
- Consistent border radius
- Consistent shadows
- Consistent animations

Never introduce random styles.

---

# Premium UI Rules

Every page must include where appropriate:

- Loading Skeletons
- Empty States
- Error States
- Hover Effects
- Smooth Transitions
- Responsive Layout
- Proper Spacing

Never show blank white screens.

Never use browser default styling.

---

# Component Rules

Always reuse components before creating new ones.

Preferred reusable components:

- PremiumCard
- ScoreBadge
- StatusPill
- PageHeader
- SectionHeader
- KPI Card
- Drawer
- Modal
- Table
- Search Box
- Pagination
- Empty State
- Skeleton Loader

If a component already exists,

extend it.

Do not duplicate it.

---

# Layout Rules

Desktop first.

Then tablet.

Then mobile.

Every page must remain usable on:

- Desktop
- Laptop
- Tablet
- Mobile

Never break responsiveness.

---

# Tables

Every enterprise table should support when applicable:

- Search
- Sorting
- Filtering
- Pagination
- Bulk Selection
- Bulk Actions
- Sticky Header
- Hover State
- Empty State
- Loading Skeleton

Never use plain HTML tables without styling.

---

# Forms

Forms should always include:

- Validation
- Loading State
- Success State
- Error State

Buttons should disable during requests.

Never allow duplicate submissions.

---

# Dashboard Rules

Dashboard is the flagship page.

Always prioritize:

- Executive KPIs
- Business Insights
- AI Metrics
- Visual Hierarchy

Charts must be readable.

Cards must have equal spacing.

---

# Lead Management Rules

Lead Management is a premium CRM.

Every improvement should preserve:

- Fast searching
- Smooth filtering
- Bulk operations
- Drawer preview
- Sticky columns
- AI score visibility

Never simplify existing CRM functionality.

---

# Lead Details Rules

Lead Details should feel like an intelligence report.

Always prioritize:

- Business overview
- AI insights
- Screenshots
- Audit
- Outreach
- Timeline

Never clutter the interface.

Information should be grouped logically.

---

# Colors

Never introduce random colors.

Reuse existing project colors.

Primary actions should remain consistent across the entire application.

Status colors should always remain consistent.

Success

Warning

Danger

Info

must never change between pages.

---

# Animation Rules

Animations should feel subtle.

Preferred duration:

150–300ms

Avoid flashy effects.

Use smooth transitions only.

Performance is more important than fancy animation.
---

# Development Workflow

For every task, always follow this workflow.

Step 1

Read CLAUDE.md completely.

Step 2

Understand today's sprint.

Step 3

Inspect ONLY the files related to today's task.

Never inspect the whole repository unless explicitly requested.

Step 4

Create a short implementation plan.

Step 5

Implement.

Step 6

Build the project.

Step 7

Fix all build errors.

Step 8

Self review.

Step 9

Provide a readiness score.

---

# AI Working Rules

Always think before coding.

Never immediately start editing files.

Understand existing code first.

Prefer improving existing implementation instead of rewriting.

Reuse existing components whenever possible.

If something already exists,

extend it.

Never duplicate functionality.

---

# Token Saving Rules

Never perform another full architecture audit.

Never scan the entire repository again unless explicitly requested.

Read only files required for today's sprint.

Reuse information from CLAUDE.md.

Keep responses focused.

Avoid unnecessary explanations.

---

# Coding Standards

Write clean, readable code.

Prefer clarity over cleverness.

Keep functions small.

Avoid duplicated logic.

Keep naming consistent.

Never leave unused imports.

Never leave commented-out code.

Never ignore TypeScript errors.

Never ignore lint/build errors.

---

# Backend Rules

Never bypass the service layer.

Never place business logic inside routes.

Never duplicate database queries.

Always reuse repositories.

Always validate inputs.

Never expose secrets.

---

# Frontend Rules

Always use existing API services.

Always keep components reusable.

Always maintain responsiveness.

Always preserve accessibility.

Never hardcode API responses.

Never fake backend data.

---

# Performance Rules

Avoid unnecessary re-renders.

Avoid duplicate API requests.

Lazy load heavy components when appropriate.

Reuse existing state whenever possible.

Keep bundle size reasonable.

---

# Security Rules

Never expose API keys.

Never hardcode secrets.

Always validate user input.

Always respect authentication.

Never bypass authorization.

---

# Before Finishing Any Sprint

Always:

- Run the build
- Fix all errors
- Check responsiveness
- Check loading states
- Check empty states
- Check error handling
- Review code quality

Only then consider the sprint complete.

---

# Things Claude Must Never Do

Never redesign the whole project unless asked.

Never remove working features.

Never change architecture without reason.

Never duplicate components.

Never duplicate API endpoints.

Never fabricate data.

Never break the design system.

Never ignore existing coding patterns.

Never leave build errors.

Never leave TODOs in production code.

Never introduce breaking changes without explaining them.

---

# Success Criteria

Every implementation should be:

- Production Ready
- Enterprise Quality
- Responsive
- Maintainable
- Reusable
- Scalable
- Build Successfully
- Consistent with the existing design system

LeadForge AI should always feel like a premium commercial SaaS.
