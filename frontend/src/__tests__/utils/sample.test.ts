/**
 * Sample utility tests to verify the testing setup works.
 *
 * These tests demonstrate the testing patterns for utility functions.
 */

import { describe, it, expect } from 'vitest'

// Sample utility functions (inline for demonstration)
function formatCurrency(amount: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  }).format(amount)
}

function calculatePercentageChange(oldValue: number, newValue: number): number {
  if (oldValue === 0) return newValue > 0 ? 100 : 0
  return ((newValue - oldValue) / oldValue) * 100
}

function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength - 3) + '...'
}

describe('Utility Functions', () => {
  describe('formatCurrency', () => {
    it('formats USD correctly', () => {
      expect(formatCurrency(1000)).toBe('$1,000.00')
    })

    it('formats large numbers with commas', () => {
      expect(formatCurrency(1000000)).toBe('$1,000,000.00')
    })

    it('formats decimal amounts correctly', () => {
      expect(formatCurrency(99.99)).toBe('$99.99')
    })

    it('handles zero', () => {
      expect(formatCurrency(0)).toBe('$0.00')
    })

    it('handles negative amounts', () => {
      expect(formatCurrency(-500)).toBe('-$500.00')
    })
  })

  describe('calculatePercentageChange', () => {
    it('calculates positive change correctly', () => {
      const result = calculatePercentageChange(100, 150)
      expect(result).toBe(50)
    })

    it('calculates negative change correctly', () => {
      const result = calculatePercentageChange(100, 75)
      expect(result).toBe(-25)
    })

    it('returns 0 for no change', () => {
      const result = calculatePercentageChange(100, 100)
      expect(result).toBe(0)
    })

    it('handles zero old value with positive new value', () => {
      const result = calculatePercentageChange(0, 100)
      expect(result).toBe(100)
    })

    it('handles zero old value with zero new value', () => {
      const result = calculatePercentageChange(0, 0)
      expect(result).toBe(0)
    })
  })

  describe('truncateText', () => {
    it('returns text unchanged if shorter than max length', () => {
      expect(truncateText('Hello', 10)).toBe('Hello')
    })

    it('returns text unchanged if equal to max length', () => {
      expect(truncateText('Hello', 5)).toBe('Hello')
    })

    it('truncates long text and adds ellipsis', () => {
      expect(truncateText('Hello World', 8)).toBe('Hello...')
    })

    it('handles empty string', () => {
      expect(truncateText('', 10)).toBe('')
    })

    it('handles very short max length', () => {
      expect(truncateText('Hello', 4)).toBe('H...')
    })
  })
})

describe('Array and Object Operations', () => {
  it('filters array correctly', () => {
    const numbers = [1, 2, 3, 4, 5]
    const evens = numbers.filter((n) => n % 2 === 0)
    expect(evens).toEqual([2, 4])
  })

  it('maps array correctly', () => {
    const numbers = [1, 2, 3]
    const doubled = numbers.map((n) => n * 2)
    expect(doubled).toEqual([2, 4, 6])
  })

  it('reduces array correctly', () => {
    const numbers = [1, 2, 3, 4, 5]
    const sum = numbers.reduce((acc, n) => acc + n, 0)
    expect(sum).toBe(15)
  })

  it('spreads objects correctly', () => {
    const original = { a: 1, b: 2 }
    const extended = { ...original, c: 3 }
    expect(extended).toEqual({ a: 1, b: 2, c: 3 })
  })

  it('destructures objects correctly', () => {
    const obj = { name: 'Test', value: 100 }
    const { name, value } = obj
    expect(name).toBe('Test')
    expect(value).toBe(100)
  })
})

describe('Async Operations', () => {
  it('resolves promises correctly', async () => {
    const promise = Promise.resolve('success')
    const result = await promise
    expect(result).toBe('success')
  })

  it('handles async/await correctly', async () => {
    const fetchData = async (): Promise<{ data: string }> => {
      return { data: 'test data' }
    }

    const result = await fetchData()
    expect(result.data).toBe('test data')
  })

  it('handles promise rejection', async () => {
    const failingPromise = Promise.reject(new Error('Test error'))

    await expect(failingPromise).rejects.toThrow('Test error')
  })
})
