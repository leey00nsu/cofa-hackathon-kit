import { ArrowUpRight, CircleDashed, Database, Layers2 } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function Home() {
  return (
    <div className="mx-auto flex min-h-svh max-w-5xl flex-col px-5 sm:px-8">
      <a href="#main" className="sr-only rounded-lg bg-primary p-3 text-primary-foreground focus:not-sr-only focus:absolute focus:top-4 focus:z-10">
        본문으로 이동
      </a>
      <header className="flex items-center justify-between gap-4 border-b py-6 sm:py-8">
        <div className="flex items-center gap-3">
          <span className="flex size-10 items-center justify-center rounded-xl bg-primary text-primary-foreground">
            <Layers2 aria-hidden="true" className="size-5" />
          </span>
          <span className="text-sm font-semibold tracking-wide">COFA <span className="font-normal text-muted-foreground">/ 시작 공간</span></span>
        </div>
        <Badge variant="outline" className="bg-card px-3 py-2">빈 스타터</Badge>
      </header>

      <main id="main" className="flex-1 py-16 sm:py-24">
        <div className="mb-12 max-w-xl">
          <p className="mb-4 text-sm font-medium text-primary">작은 시작, 새로운 가능성</p>
          <h1 className="text-4xl leading-tight font-semibold tracking-tight text-balance sm:text-6xl">새 프로젝트</h1>
          <p className="mt-6 max-w-md text-base leading-8 text-muted-foreground sm:text-lg">
            아이디어를 채워 넣을 준비가 된 공간입니다.<br className="hidden sm:block" />
            필요한 기능을 이곳에서 하나씩 만들어 보세요.
          </p>
        </div>

        <div className="grid items-stretch gap-5 md:grid-cols-[1.35fr_1fr]">
          <Card className="gap-6 rounded-2xl py-7 shadow-xs [--card-spacing:--spacing(7)]">
            <CardHeader className="gap-3">
              <span className="mb-2 flex size-10 items-center justify-center rounded-xl bg-secondary text-primary">
                <CircleDashed aria-hidden="true" className="size-5" />
              </span>
              <CardTitle><h2 className="text-xl">여기서부터 시작하세요</h2></CardTitle>
              <CardDescription className="leading-7">아직 업무 기능이 없는 빈 시작 화면입니다.<br />실제 요구사항에 맞춰 화면과 동작을 추가하세요.</CardDescription>
            </CardHeader>
            <CardContent>
              <Badge variant="secondary" className="px-3 py-2">업무 기능 미구현</Badge>
            </CardContent>
          </Card>

          <Card className="gap-6 rounded-2xl bg-secondary/40 py-7 shadow-none [--card-spacing:--spacing(7)]">
            <CardHeader className="gap-3">
              <span className="mb-2 flex size-10 items-center justify-center rounded-xl border bg-card text-primary">
                <Database aria-hidden="true" className="size-5" />
              </span>
              <CardTitle><h2 className="text-xl">연결을 확인할 수 있어요</h2></CardTitle>
              <CardDescription className="leading-7">데이터베이스 연결 상태를 확인합니다.<br />결과는 JSON 형식으로 열립니다.</CardDescription>
            </CardHeader>
            <CardContent>
              <Button asChild className="min-h-11 w-full gap-2 sm:w-auto">
                <a href="/api/health">DB 연결 상태 확인<ArrowUpRight aria-hidden="true" /></a>
              </Button>
            </CardContent>
          </Card>
        </div>

        <Alert role="note" className="mt-6 border-dashed bg-transparent px-5 py-4">
          <AlertTitle>연결 확인과 업무 완료는 다릅니다</AlertTitle>
          <AlertDescription className="mt-1 leading-7">연결 성공은 데이터베이스가 응답했다는 뜻입니다. 업무 기능의 구현이나 검증이 끝났다는 뜻은 아닙니다.</AlertDescription>
        </Alert>
      </main>

      <footer className="flex flex-col gap-2 border-t py-6 text-xs leading-6 text-muted-foreground sm:flex-row sm:justify-between">
        <span>새로운 작업을 위한 빈 시작점</span>
        <span>shadcn/ui 디자인 구성 요소 포함</span>
      </footer>
    </div>
  );
}
