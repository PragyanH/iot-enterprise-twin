"use client";

import React, { createContext, useContext, useEffect, useState } from "react";

type Theme = "dark" | "light";

interface ThemeContextType {
 theme: Theme;
 toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
 const [theme, setTheme] = useState<Theme>("dark");

 useEffect(() => {
 const savedTheme = localStorage.getItem("aegis-theme") as Theme | null;
 if (savedTheme) {
 setTheme(savedTheme);
 document.documentElement.setAttribute("data-theme", savedTheme);
 } else {
 document.documentElement.setAttribute("data-theme", "dark");
 }
 }, []);

 const toggleTheme = () => {
 const nextTheme = theme === "dark" ? "light" : "dark";
 setTheme(nextTheme);
 localStorage.setItem("aegis-theme", nextTheme);
 document.documentElement.setAttribute("data-theme", nextTheme);
 };

 return (
 <ThemeContext.Provider value={{ theme, toggleTheme }}>
 {children}
 </ThemeContext.Provider>
 );
}

export function useTheme() {
 const context = useContext(ThemeContext);
 if (!context) {
 throw new Error("useTheme must be used within a ThemeProvider");
 }
 return context;
}
