"use client"

import { Brain, Zap, Target, ArrowUpRight } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"

export function AIControlCenter() {
    return (
        <Card className="border-none bg-gradient-to-br from-indigo-600 to-violet-700 text-white shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 p-8 opacity-10">
                <Brain className="h-32 w-32" />
            </div>
            <CardHeader>
                <div className="flex items-center gap-2 mb-1">
                    <div className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                    <span className="text-[10px] font-black tracking-widest uppercase opacity-70">AI Engine Active</span>
                </div>
                <CardTitle className="text-2xl font-black">Центр управления интеллектом</CardTitle>
                <CardDescription className="text-indigo-100/70 italic text-xs">
                    Bảng điều khiển trí tuệ nhân tạo NeuroSupply
                </CardDescription>
            </CardHeader>
            <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-4">
                    <div className="flex flex-col gap-1 p-4 rounded-2xl bg-white/10 backdrop-blur-md border border-white/10 group hover:bg-white/20 transition-all cursor-default">
                        <div className="flex items-center justify-between">
                            <Target className="h-5 w-5 text-emerald-400" />
                            <ArrowUpRight className="h-4 w-4 opacity-30 group-hover:opacity-100 transition-opacity" />
                        </div>
                        <div className="mt-2">
                            <p className="text-2xl font-bold">94.2%</p>
                            <p className="text-[10px] font-medium opacity-70 uppercase tracking-wider">Точность прогноза</p>
                            <p className="text-[8px] italic opacity-50">Độ chính xác dự báo</p>
                        </div>
                    </div>

                    <div className="flex flex-col gap-1 p-4 rounded-2xl bg-white/10 backdrop-blur-md border border-white/10 group hover:bg-white/20 transition-all cursor-default">
                        <div className="flex items-center justify-between">
                            <Zap className="h-5 w-5 text-amber-400" />
                            <ArrowUpRight className="h-4 w-4 opacity-30 group-hover:opacity-100 transition-opacity" />
                        </div>
                        <div className="mt-2">
                            <p className="text-2xl font-bold">~14 ч/мес</p>
                            <p className="text-[10px] font-medium opacity-70 uppercase tracking-wider">Экономия времени</p>
                            <p className="text-[8px] italic opacity-50">Tiết kiệm thời gian</p>
                        </div>
                    </div>

                    <div className="flex flex-col gap-1 p-4 rounded-2xl bg-white/10 backdrop-blur-md border border-white/10 group hover:bg-white/20 transition-all cursor-default">
                        <div className="flex items-center justify-between">
                            <Brain className="h-5 w-5 text-indigo-300" />
                            <ArrowUpRight className="h-4 w-4 opacity-30 group-hover:opacity-100 transition-opacity" />
                        </div>
                        <div className="mt-2">
                            <p className="text-2xl font-bold">v2.4.0</p>
                            <p className="text-[10px] font-medium opacity-70 uppercase tracking-wider">Модель Llama-3-8B</p>
                            <p className="text-[8px] italic opacity-50">Phiên bản mô hình AI</p>
                        </div>
                    </div>
                </div>

                <div className="mt-8 p-4 rounded-2xl bg-emerald-500/20 border border-emerald-500/30 flex items-center gap-4">
                    <div className="h-10 w-10 rounded-full bg-emerald-500 flex items-center justify-center rotate-12">
                        <ArrowUpRight className="h-6 w-6 text-white" />
                    </div>
                    <div>
                        <p className="text-xs font-bold font-mono">INSIGHT: Спрос на Фо Бо вырастет на 20% в пятницу вечером</p>
                        <p className="text-[10px] opacity-70 italic">Dự báo: Nhu cầu Phở Bò sẽ tăng 20% vào chiều tối thứ Sáu</p>
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}
