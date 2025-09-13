import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useRouter, useSearchParams } from 'next/navigation'
import LoginPage from '@/app/auth/login/page'
import { useAuth } from '@/contexts/AuthContext'

// Mock Next.js navigation
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  useSearchParams: jest.fn(),
}))

// Mock AuthContext
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(),
}))

const mockPush = jest.fn()
const mockSignIn = jest.fn()

describe('LoginPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
    })
    ;(useSearchParams as jest.Mock).mockReturnValue({
      get: jest.fn().mockReturnValue('/dashboard'),
    })
    ;(useAuth as jest.Mock).mockReturnValue({
      signIn: mockSignIn,
    })
  })

  it('renders login form', () => {
    render(<LoginPage />)
    
    expect(screen.getByText('Sign in to ZERO-COMP')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Email address')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Password')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeInTheDocument()
  })

  it('handles successful login', async () => {
    mockSignIn.mockResolvedValue({ error: null })
    
    render(<LoginPage />)
    
    fireEvent.change(screen.getByPlaceholderText('Email address'), {
      target: { value: 'test@example.com' },
    })
    fireEvent.change(screen.getByPlaceholderText('Password'), {
      target: { value: 'password123' },
    })
    
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    
    await waitFor(() => {
      expect(mockSignIn).toHaveBeenCalledWith('test@example.com', 'password123')
      expect(mockPush).toHaveBeenCalledWith('/dashboard')
    })
  })

  it('displays error message on failed login', async () => {
    const errorMessage = 'Invalid credentials'
    mockSignIn.mockResolvedValue({ error: { message: errorMessage } })
    
    render(<LoginPage />)
    
    fireEvent.change(screen.getByPlaceholderText('Email address'), {
      target: { value: 'test@example.com' },
    })
    fireEvent.change(screen.getByPlaceholderText('Password'), {
      target: { value: 'wrongpassword' },
    })
    
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    
    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })
  })

  it('shows loading state during login', async () => {
    mockSignIn.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))
    
    render(<LoginPage />)
    
    fireEvent.change(screen.getByPlaceholderText('Email address'), {
      target: { value: 'test@example.com' },
    })
    fireEvent.change(screen.getByPlaceholderText('Password'), {
      target: { value: 'password123' },
    })
    
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    
    expect(screen.getByText('Signing in...')).toBeInTheDocument()
  })
})