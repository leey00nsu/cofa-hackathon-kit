import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "새 프로젝트",
  description: "기본 화면과 디자인 구성 요소를 갖춘 빈 시작 공간",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="ko"><body>{children}</body></html>;
}
