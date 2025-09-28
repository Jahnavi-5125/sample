// app/layout.tsx
'use client';

import { Schibsted_Grotesk } from 'next/font/google';
import './globals.css';
import './styles.css';
import { Toaster } from 'sonner';
import { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { verifyToken } from '@/utils/auth';
import { useAuthStore } from '@/store/useZustandStore';
import LoaderComponent from '@/components/Loader';
import NextTopLoader from 'nextjs-toploader';
import Head from 'next/head';
import Link from 'next/link';
import { getPreferences } from '@/services/prefs';

const fustat = Schibsted_Grotesk({
  variable: '--font-fustat',
  subsets: ['latin'],
  weight: ['400', '500', '600', '700', '800'],
});

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const [isLoading, setIsLoading] = useState(true);
  const pathname = usePathname();
  const router = useRouter();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const [isDark, setIsDark] = useState(false);

  const noSidebarPages = ['/login', '/signup', '/reset-password', '/onbording', '/preferences', '/dashboard'];

  useEffect(() => {
    const checkAuth = async () => {
      setIsLoading(true);

      // Skip verification if already authenticated in store
      if (isAuthenticated && !noSidebarPages.includes(pathname)) {
        setIsLoading(false);
        return;
      }

      // Otherwise verify the token
      const isValid = await verifyToken();

      if (isValid) {
        if (noSidebarPages.includes(pathname)) {
          router.push('/');
        }
      } else {
        if (!noSidebarPages.includes(pathname)) {
          router.push('/login');
        }
      }

      setIsLoading(false);
    };

    checkAuth();
  }, [pathname, router, isAuthenticated]);

  // Load saved theme globally (default_user)
  useEffect(() => {
    const loadTheme = async () => {
      try {
        const res = await getPreferences('default_user');
        const theme = (res?.preferences as any)?.theme as 'light' | 'dark' | undefined;
        setIsDark(theme === 'dark');
      } catch {
        // ignore failures; default remains light
      }
    };
    loadTheme();
  }, []);

  return (
    <html lang="en" className={`${fustat.variable} ${isDark ? 'dark' : ''}`}>
      <Head>
        <link rel="apple-touch-icon" sizes="57x57" href="/apple-icon-57x57.png" />
        <link rel="apple-touch-icon" sizes="114x114" href="/apple-icon-114x114.png" />
        <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
        <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
        <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png" />
        <title>hiiiiiiiiiiiiiiiii</title>
      </Head>
      <body>
        {/* NextTopLoader should always be rendered */}
        <NextTopLoader
          color="#954767"
          initialPosition={0.08}
          crawlSpeed={200}
          height={3}
          crawl={true}
          showSpinner={false}
          easing="ease"
          speed={200}
          shadow="0 0 10px #954767,0 0 5px #954767"
        />

        {isLoading ? (
          <LoaderComponent />
        ) : (
          <>
            <header className="w-full border-b bg-white/80 backdrop-blur sticky top-0 z-30">
              <nav className="max-w-6xl mx-auto flex items-center justify-between px-4 py-3">
                <div className="text-lg font-semibold text-indigo-700">Finance Insights</div>
                <div className="flex items-center gap-4">
                  <Link href="/preferences" className="text-sm text-gray-700 hover:text-indigo-700">Preferences</Link>
                  <Link href="/dashboard" className="text-sm text-gray-700 hover:text-indigo-700">Dashboard</Link>
                </div>
              </nav>
            </header>

            <main className="max-w-6xl mx-auto px-4 py-6">{children}</main>
            <Toaster richColors position="top-center" />
          </>
        )}
      </body>
    </html>
  );
}
