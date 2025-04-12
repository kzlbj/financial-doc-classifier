import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import axios from 'axios';
import Login from './Login';

// 模拟axios
jest.mock('axios');

// 包装在Router中以支持useNavigate
const renderWithRouter = (ui, { route = '/' } = {}) => {
  window.history.pushState({}, 'Test page', route);
  return render(ui, { wrapper: BrowserRouter });
};

describe('Login Component', () => {
  beforeEach(() => {
    // 清除所有模拟
    jest.clearAllMocks();
    // 模拟localStorage
    const localStorageMock = {
      getItem: jest.fn(),
      setItem: jest.fn(),
      clear: jest.fn()
    };
    global.localStorage = localStorageMock;
  });

  test('renders login form', () => {
    renderWithRouter(<Login />);
    
    // 检查标题是否存在
    expect(screen.getByText(/登录/i)).toBeInTheDocument();
    
    // 检查表单元素是否存在
    expect(screen.getByLabelText(/邮箱/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/密码/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /登录/i })).toBeInTheDocument();
  });

  test('handles form submission correctly', async () => {
    // 模拟成功响应
    axios.post.mockResolvedValueOnce({ 
      data: { 
        access_token: 'test_token',
        token_type: 'bearer'
      } 
    });
    
    renderWithRouter(<Login />);
    
    // 输入登录信息
    fireEvent.change(screen.getByLabelText(/邮箱/i), {
      target: { value: 'test@example.com' }
    });
    
    fireEvent.change(screen.getByLabelText(/密码/i), {
      target: { value: 'password123' }
    });
    
    // 提交表单
    fireEvent.click(screen.getByRole('button', { name: /登录/i }));
    
    // 验证API调用
    await waitFor(() => {
      expect(axios.post).toHaveBeenCalledWith(
        '/api/auth/login',
        { username: 'test@example.com', password: 'password123' }
      );
    });
    
    // 验证localStorage存储token
    await waitFor(() => {
      expect(localStorage.setItem).toHaveBeenCalledWith(
        'token',
        'test_token'
      );
    });
  });

  test('displays error message on login failure', async () => {
    // 模拟失败响应
    axios.post.mockRejectedValueOnce({
      response: {
        status: 401,
        data: { detail: '邮箱或密码不正确' }
      }
    });
    
    renderWithRouter(<Login />);
    
    // 输入登录信息
    fireEvent.change(screen.getByLabelText(/邮箱/i), {
      target: { value: 'test@example.com' }
    });
    
    fireEvent.change(screen.getByLabelText(/密码/i), {
      target: { value: 'wrongpassword' }
    });
    
    // 提交表单
    fireEvent.click(screen.getByRole('button', { name: /登录/i }));
    
    // 验证错误信息显示
    await waitFor(() => {
      expect(screen.getByText(/邮箱或密码不正确/i)).toBeInTheDocument();
    });
  });

  test('validates form inputs', async () => {
    renderWithRouter(<Login />);
    
    // 直接点击登录按钮，不填写任何内容
    fireEvent.click(screen.getByRole('button', { name: /登录/i }));
    
    // 验证表单验证错误信息
    await waitFor(() => {
      expect(screen.getByText(/邮箱是必填的/i)).toBeInTheDocument();
      expect(screen.getByText(/密码是必填的/i)).toBeInTheDocument();
    });
    
    // 输入无效的邮箱
    fireEvent.change(screen.getByLabelText(/邮箱/i), {
      target: { value: 'invalid-email' }
    });
    
    // 验证邮箱验证错误
    await waitFor(() => {
      expect(screen.getByText(/邮箱格式无效/i)).toBeInTheDocument();
    });
  });
}); 