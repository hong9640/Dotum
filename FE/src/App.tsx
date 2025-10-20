import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import { Button } from '@/components/ui/button'
import { IconGitBranch } from "@tabler/icons-react"
import { ArrowUpIcon, CatIcon } from "lucide-react"

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
      <div className="w-full text-center">
        <h1 className="text-3xl font-sans font-bold text-blue-600">
          Pretendard 적용 완료 🎉
        </h1>
        <p className="text-gray-500 mt-2">
          Tailwind 3.4.17 + Pretendard 폰트 세팅 성공!
        </p>
        <div className="flex justify-center items-center">
          <a href="https://vite.dev" target="_blank">
            <img src={viteLogo} className="logo" alt="Vite logo" />
          </a>
          <a href="https://react.dev" target="_blank">
            <img src={reactLogo} className="logo react" alt="React logo" />
          </a>
        </div>
        <div className="flex justify-center items-center gap-2">
          {/* <div className="flex items-center justify-center w-40 h-12 bg-green-900 rounded-lg">
            <p className="font-bold text-lg !text-white">Hello</p>
          </div> */}
          <Button variant="default" size="lg" >
            <CatIcon /> New Branch
          </Button>
          <div className="flex min-h-svh flex-col items-center justify-center">
            <Button size="lg" variant="outline">Click me</Button>
          </div>

        </div>
      </div>
      {/* <h1>Vite + React</h1> */}
      {/* <div className="card">
        <button onClick={() => setCount((count) => count + 1)}>
          count is {count}
        </button>
        <p>
          Edit <code>src/App.tsx</code> and save to test HMR
        </p>
      </div>
      <p className="read-the-docs">
        Click on the Vite and React logos to learn more
      </p> */}

    </>

  )
}

export default App
