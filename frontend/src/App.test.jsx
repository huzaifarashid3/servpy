import React from "react";
import { render, screen } from '@testing-library/react';
import App from './App';
import {describe, it, expect} from 'vitest';

describe('App', () => {
  it('renders upload form', () => {
    render(<App />);
    expect(screen.getByText(/Upload Microservice/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Microservice Name/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Description/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Upload/i })).toBeInTheDocument();
  });
});
