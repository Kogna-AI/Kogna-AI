/**
 * Sample component tests to verify the testing setup works.
 *
 * These tests demonstrate the testing patterns for React components.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import React from 'react'

// Sample components for testing (inline for demonstration)
interface ButtonProps {
  onClick: () => void
  children: React.ReactNode
  disabled?: boolean
}

function Button({ onClick, children, disabled = false }: ButtonProps) {
  return (
    <button type="button" onClick={onClick} disabled={disabled}>
      {children}
    </button>
  )
}

interface InputProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
}

function Input({ value, onChange, placeholder }: InputProps) {
  return (
    <input
      type="text"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
    />
  )
}

interface CardProps {
  title: string
  description: string
  onClick?: () => void
}

function Card({ title, description, onClick }: CardProps) {
  return (
    <div onClick={onClick} role={onClick ? 'button' : undefined}>
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
  )
}

describe('Button Component', () => {
  it('renders with text', () => {
    render(<Button onClick={() => {}}>Click me</Button>)

    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument()
  })

  it('calls onClick when clicked', async () => {
    const handleClick = vi.fn()
    const user = userEvent.setup()

    render(<Button onClick={handleClick}>Click me</Button>)

    await user.click(screen.getByRole('button'))

    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('does not call onClick when disabled', async () => {
    const handleClick = vi.fn()
    const user = userEvent.setup()

    render(
      <Button onClick={handleClick} disabled>
        Click me
      </Button>
    )

    await user.click(screen.getByRole('button'))

    expect(handleClick).not.toHaveBeenCalled()
  })

  it('has disabled attribute when disabled prop is true', () => {
    render(
      <Button onClick={() => {}} disabled>
        Click me
      </Button>
    )

    expect(screen.getByRole('button')).toBeDisabled()
  })
})

describe('Input Component', () => {
  it('renders with placeholder', () => {
    render(<Input value="" onChange={() => {}} placeholder="Enter text..." />)

    expect(screen.getByPlaceholderText('Enter text...')).toBeInTheDocument()
  })

  it('displays value correctly', () => {
    render(<Input value="test value" onChange={() => {}} />)

    expect(screen.getByRole('textbox')).toHaveValue('test value')
  })

  it('calls onChange when typing', async () => {
    const handleChange = vi.fn()
    const user = userEvent.setup()

    render(<Input value="" onChange={handleChange} />)

    await user.type(screen.getByRole('textbox'), 'hello')

    // onChange is called for each character
    expect(handleChange).toHaveBeenCalledTimes(5)
    expect(handleChange).toHaveBeenLastCalledWith('o')
  })

  it('handles controlled input correctly', () => {
    const { rerender } = render(<Input value="initial" onChange={() => {}} />)

    expect(screen.getByRole('textbox')).toHaveValue('initial')

    rerender(<Input value="updated" onChange={() => {}} />)

    expect(screen.getByRole('textbox')).toHaveValue('updated')
  })
})

describe('Card Component', () => {
  it('renders title and description', () => {
    render(<Card title="Test Title" description="Test Description" />)

    expect(screen.getByRole('heading', { name: /test title/i })).toBeInTheDocument()
    expect(screen.getByText(/test description/i)).toBeInTheDocument()
  })

  it('is clickable when onClick is provided', async () => {
    const handleClick = vi.fn()
    const user = userEvent.setup()

    render(
      <Card
        title="Clickable Card"
        description="Click me"
        onClick={handleClick}
      />
    )

    await user.click(screen.getByRole('button'))

    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('is not a button when onClick is not provided', () => {
    render(<Card title="Static Card" description="Not clickable" />)

    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })
})

describe('Component Snapshots', () => {
  it('Button matches snapshot', () => {
    const { container } = render(<Button onClick={() => {}}>Snapshot Test</Button>)

    expect(container).toMatchSnapshot()
  })

  it('Card matches snapshot', () => {
    const { container } = render(
      <Card title="Snapshot Title" description="Snapshot Description" />
    )

    expect(container).toMatchSnapshot()
  })
})

describe('Component Accessibility', () => {
  it('button is focusable', async () => {
    const user = userEvent.setup()

    render(<Button onClick={() => {}}>Focusable</Button>)

    await user.tab()

    expect(screen.getByRole('button')).toHaveFocus()
  })

  it('input is focusable', async () => {
    const user = userEvent.setup()

    render(<Input value="" onChange={() => {}} />)

    await user.tab()

    expect(screen.getByRole('textbox')).toHaveFocus()
  })
})
