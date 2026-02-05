// frontend/src/app/components/LandingNavbar.tsx
"use client";

import React from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';
import { Button } from '../ui/button';

export function LandingNavbar() {
  const router = useRouter();
  const pathname = usePathname();

  const handleNavClick = (e: React.MouseEvent<HTMLAnchorElement>, id: string) => {
    // If we are already on the landing page, just scroll smoothly
    if (pathname === '/') {
      e.preventDefault();
      const element = document.getElementById(id);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
      }
    } 
    // If we are on /login or /signup, the "href" will naturally take us to "/#id"
    // Next.js/Browsers handle the jump to the ID automatically on page load.
  };

  return (
    <header className="sticky top-0 z-50 w-auto border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4 md:px-6 h-16 flex items-center justify-between">
        
        {/* Left Side: Logo & Navigation */}
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-2 font-bold text-xl tracking-tight cursor-pointer">
            <Image 
              src="/KognaKLetterLogo.png" 
              alt="Kogna Logo" 
              width={32} 
              height={32} 
              className="object-contain"
            />
            <span>Kogna</span>
          </Link>
          
          <nav className="hidden md:flex items-center gap-6">
            <a 
              href="/#features" 
              onClick={(e) => handleNavClick(e, 'features')} 
              className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors"
            >
              Product
            </a>
            <a 
              href="/#how-it-works" 
              onClick={(e) => handleNavClick(e, 'how-it-works')} 
              className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors"
            >
              How it Works
            </a>
            <a 
              href="/#pricing" 
              onClick={(e) => handleNavClick(e, 'pricing')} 
              className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors"
            >
              Pricing
            </a>
          </nav>
        </div>

        {/* Right Side: Actions */}
        <div className="flex items-center justify-end lg:justify-center gap-4 w-auto lg:w-[400px]">
          <a 
            href="https://calendly.com/getkogna/30min" 
            target="_blank" 
            rel="noopener noreferrer"
            className="hidden md:flex items-center gap-2 text-sm font-medium hover:text-primary/80"
          >
            Book a demo
          </a>
          <Button onClick={() => router.push("/signup/waitlist")} size="sm" className="hidden sm:flex transition-transform hover:scale-105">
            Join Waitlist
          </Button>
          <div className="w-px h-6 bg-border mx-1 hidden sm:block"></div>
          <Button variant="ghost" size="sm" onClick={() => router.push("/login")}>
            Log in
          </Button>
        </div>
      </div>
    </header>
  );
}