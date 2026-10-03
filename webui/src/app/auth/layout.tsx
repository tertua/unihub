import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Faculty Learning Hub',
  description: 'Sign in to Faculty Learning Hub',
  robots: {
    index: false,
    follow: false
  }
};

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return children;
}
