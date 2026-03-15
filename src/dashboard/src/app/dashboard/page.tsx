"use client"

import { ShoppingCart, Package, AlertTriangle, TrendingUp, Loader2 } from "lucide-react"
import { api, DashboardSummary } from "@/lib/api"
import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { AIControlCenter } from "@/components/AIControlCenter"

export default function DashboardPage() {
    const [summary, setSummary] = useState<DashboardSummary | null>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        api.getSummary()
            .then(setSummary)
            .finally(() => setLoading(false))
    }, [])
    return (
        <div className="space-y-8 pb-10">
            <div className="flex flex-col gap-1">
                <h1 className="text-4xl md:text-5xl font-black tracking-tighter bg-gradient-to-r from-foreground to-foreground/60 bg-clip-text text-transparent uppercase">
                    Обзор системы
                </h1>
                <p className="text-muted-foreground text-lg font-medium">
                    Панель управления NeuroSupply.
                    <span className="ml-2 text-xs italic opacity-40 font-normal uppercase tracking-widest">Tổng quan hệ thống</span>
                </p>
            </div>

            <AIControlCenter />

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
                <Card className="relative overflow-hidden border-none bg-gradient-to-br from-blue-500/10 to-blue-500/5 shadow-xl hover:scale-[1.02] transition-transform cursor-default group">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-bold uppercase tracking-wider opacity-70">Активные заказы</CardTitle>
                        <ShoppingCart className="h-4 w-4 text-blue-500 group-hover:scale-110 transition-transform" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-3xl font-black tracking-tight">
                            {loading ? <Loader2 className="h-6 w-6 animate-spin" /> : summary?.active_orders}
                        </div>
                        <div className="flex items-center gap-2 mt-2">
                            <Badge variant="secondary" className="bg-blue-500/20 text-blue-500 hover:bg-blue-500/30 font-bold">
                                В РАБОТЕ
                            </Badge>
                            <span className="text-[10px] text-muted-foreground italic opacity-50 uppercase tracking-tighter">Đơn hàng</span>
                        </div>
                    </CardContent>
                    <div className="absolute -right-4 -bottom-4 h-24 w-24 bg-blue-500/10 blur-3xl rounded-full" />
                </Card>

                <Card className="relative overflow-hidden border-none bg-gradient-to-br from-purple-500/10 to-purple-500/5 shadow-xl hover:scale-[1.02] transition-transform cursor-default group">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-bold uppercase tracking-wider opacity-70">Товары на складе</CardTitle>
                        <Package className="h-4 w-4 text-purple-500 group-hover:scale-110 transition-transform" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-3xl font-black tracking-tight">
                            {loading ? <Loader2 className="h-6 w-6 animate-spin" /> : summary?.total_products.toLocaleString()}
                        </div>
                        <div className="flex items-center gap-2 mt-2">
                            <Badge variant="secondary" className="bg-purple-500/20 text-purple-500 hover:bg-purple-500/30 font-bold">
                                SYNCED
                            </Badge>
                            <span className="text-[10px] text-muted-foreground italic opacity-50 uppercase tracking-tighter">Hàng trong kho</span>
                        </div>
                    </CardContent>
                    <div className="absolute -right-4 -bottom-4 h-24 w-24 bg-purple-500/10 blur-3xl rounded-full" />
                </Card>

                <Card className="relative overflow-hidden border-none bg-gradient-to-br from-amber-500/10 to-amber-500/5 shadow-xl hover:scale-[1.02] transition-transform cursor-default group border-l-4 border-l-amber-500/20">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-bold uppercase tracking-wider opacity-70">Аномалии сегодня</CardTitle>
                        <AlertTriangle className="h-4 w-4 text-amber-500 group-hover:animate-bounce" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-3xl font-black tracking-tight">
                            {loading ? <Loader2 className="h-6 w-6 animate-spin" /> : summary?.anomalies_today}
                        </div>
                        <div className="flex items-center gap-2 mt-2">
                            <Badge variant="destructive" className="bg-amber-500/20 text-amber-500 hover:bg-amber-500/30 font-bold">
                                {summary?.anomalies_today && summary.anomalies_today > 0 ? 'ВНИМАНИЕ' : 'OK'}
                            </Badge>
                            <span className="text-[10px] text-muted-foreground italic opacity-50 uppercase tracking-tighter">Bất thường</span>
                        </div>
                    </CardContent>
                    <div className="absolute -right-4 -bottom-4 h-24 w-24 bg-amber-500/10 blur-3xl rounded-full" />
                </Card>

                <Card className="relative overflow-hidden border-none bg-gradient-to-br from-emerald-500/10 to-emerald-500/5 shadow-xl hover:scale-[1.02] transition-transform cursor-default group">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-bold uppercase tracking-wider opacity-70">Экономия AI</CardTitle>
                        <TrendingUp className="h-4 w-4 text-emerald-500 group-hover:scale-110 transition-transform" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-3xl font-black tracking-tight text-emerald-500">
                            {loading ? <Loader2 className="h-6 w-6 animate-spin" /> : `${summary?.ai_savings_pct}%`}
                        </div>
                        <div className="flex items-center gap-2 mt-2">
                            <Badge variant="secondary" className="bg-emerald-500/20 text-emerald-500 hover:bg-emerald-500/30 font-bold">
                                ЕЖЕМЕСЯЧНО
                            </Badge>
                            <span className="text-[10px] text-muted-foreground italic opacity-50 uppercase tracking-tighter">Tiết kiệm AI</span>
                        </div>
                    </CardContent>
                    <div className="absolute -right-4 -bottom-4 h-24 w-24 bg-emerald-500/10 blur-3xl rounded-full" />
                </Card>
            </div>


            <div className="grid gap-4 md:grid-cols-2">
                <Card className="bg-[#0A0A0A] border-white/5 hover:border-blue-500/10 transition-colors">
                    <CardHeader className="border-b border-white/5">
                        <CardTitle className="text-lg font-bold flex items-center">
                            <TrendingUp className="w-5 h-5 mr-3 text-blue-500" />
                            Последние действия
                        </CardTitle>
                        <CardDescription>Лог изменений и уведомлений системы</CardDescription>
                    </CardHeader>
                    <CardContent className="p-0">
                        <div className="divide-y divide-white/5">
                            {[1, 2, 3].map((i) => (
                                <div key={i} className="flex items-center gap-4 p-4 hover:bg-white/[0.02] transition-colors">
                                    <div className="h-10 w-10 rounded-xl bg-blue-500/10 flex items-center justify-center">
                                        <Package className="h-5 w-5 text-blue-500" />
                                    </div>
                                    <div className="flex-1 space-y-1">
                                        <p className="text-sm font-bold text-white uppercase tracking-tight">Синхронизация завершена</p>
                                        <p className="text-xs text-neutral-500">Обновлено 128 позиций товаров</p>
                                    </div>
                                    <span className="text-xs text-neutral-500 font-mono">12:30</span>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                <Card className="bg-[#0A0A0A] border-white/5 hover:border-emerald-500/10 transition-colors">
                    <CardHeader className="border-b border-white/5">
                        <CardTitle className="text-lg font-bold">Статус Iiko Cloud</CardTitle>
                        <CardDescription>Подключение к облачным серверам</CardDescription>
                    </CardHeader>
                    <CardContent className="flex items-center justify-center p-12">
                        <div className="flex flex-col items-center gap-6">
                            <div className="relative">
                                <div className="h-24 w-24 rounded-full border-4 border-emerald-500/20 animate-pulse" />
                                <div className="absolute inset-0 flex items-center justify-center">
                                    <div className="h-16 w-16 rounded-full bg-emerald-500 flex items-center justify-center text-white font-black text-xl shadow-[0_0_30px_rgba(16,185,129,0.4)]">
                                        OK
                                    </div>
                                </div>
                            </div>
                            <div className="text-center">
                                <p className="font-bold text-emerald-500 uppercase tracking-widest text-lg">ONLINE</p>
                                <p className="text-xs text-neutral-500 mt-1 uppercase">Задержка: 42ms</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div >
    )
}
