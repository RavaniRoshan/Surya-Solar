import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import SignupPage from '@/app/auth/signup/page'
import { useAuth } from '@/contexts/AuthContext'

// Mock Next.js navigation
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}))

// Mock AuthContext
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(),
}))

const mockPush = jest.fn()
const mockSignUp = jest.fn()

describe('SignupPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
    })
    ;(useAuth as jest.Mock).mockReturnValue({
      signUp: mockSignUp,
    })
  })

  it('renders signup form', () => {
    render(<SignupPage />)
    
    expect(screen.getByText('Create your ZERO-COMP account')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Enter your email')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Create a password')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Confirm your password')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Create account' })).toBeInTheDocument()
  })

  it('handles successful signup', async () => {
    mockSignUp.mockResolvedValue({ error: null })
    
    render(<SignupPage />)
    
    fireEvent.change(screen.getByPlaceholderText('Enter your email'), {
      target: { value: 'test@example.com' },
    })
    fireEvent.change(screen.getByPlaceholderText('Create a password'), {
      target: { value: 'password123' },
    })
    fireEvent.change(screen.getByPlaceholderText('Confirm your password'), {
      target: { value: 'password123' },
    })
    
    fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
    
    await waitFor(() => {
      expect(mockSignUp).toHaveBeenCalledWith('test@example.com', 'password123')
      expect(screen.getByText('Check your email')).toBeInTheDocument()
    })
  })

  it('shows error when passwords do not match', async () => {
    render(<SignupPage />)
    
    fireEvent.change(screen.getByPlaceholderText('Enter your email'), {
      target: { value: 'test@example.com' },
    })
    fireEvent.change(screen.getByPlaceholderText('Create a password'), {
      target: { value: 'password123' },
    })
    fireEvent.change(screen.getByPlaceholderText('Confirm your password'), {
      target: { value: 'differentpassword' },
    })
    
    fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
    
    await waitFor(() => {
      expect(screen.getByText('Passwords do not match')).toBeInTheDocument()
    })
  })

  it('shows error for short password', async () => {
    render(<SignupPage />)
    
    fireEvent.change(screen.getByPlaceholderText('Enter your email'), {
      target: { value: 'test@example.com' },
    })
    fireEvent.change(screen.getByPlaceholderText('Create a password'), {
      target: { value: '123' },
    })
    fireEvent.change(screen.getByPlaceholderText('Confirm your password'), {
      target: { value: '123' },
    })
    
    fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
    
    await waitFor(() => {
      expect(screen.getByText('Password must be at least 6 characters')).toBeInTheDocument()
    })
  })

  it('displays error message on failed signup', async () => {
    const errorMessage = 'Email already exists'
    mockSignUp.mockResolvedValue({ error: { message: errorMessage } })
    
    render(<SignupPage />)
    
    fireEvent.change(screen.getByPlaceholderText('Enter your email'), {
      target: { value: 'test@example.com' },
    })
    fireEvent.change(screen.getByPlaceholderText('Create a password'), {
      target: { value: 'password123' },
    })
    fireEvent.change(screen.getByPlaceholderText('Confirm your password'), {
      target: { value: 'password123' },
    })
    
    fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
    
    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })
  })
})