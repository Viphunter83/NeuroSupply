import { ShoppingCart, Package, AlertTriangle, TrendingUp, Loader2 } from "lucide-react"
import { api, DashboardSummary } from "@/lib/api"
import { useEffect, useState } from "react"

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
            <div className="flex flex-col gap-2">
                <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/60 bg-clip-text text-transparent">
                    Обзор системы / Tổng quan hệ thống
                </h1>
                <p className="text-muted-foreground text-lg">
                    Добро пожаловать в панель управления NeuroSupply.
                    <span className="block text-sm italic opacity-70">Chào mừng bạn đến với bảng điều khiển NeuroSupply.</span>
                </p>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card className="relative overflow-hidden border-none bg-gradient-to-br from-blue-500/10 to-blue-500/5 shadow-xl">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Активные заказы</CardTitle>
                        <ShoppingCart className="h-4 w-4 text-blue-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {loading ? <Loader2 className="h-6 w-6 animate-spin" /> : summary?.active_orders}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                            Đơn hàng đang hoạt động
                        </p>
                        <Badge variant="secondary" className="mt-2 bg-blue-500/20 text-blue-500 hover:bg-blue-500/30">
                            В работе
                        </Badge>
                    </CardContent>
                    <div className="absolute -right-4 -bottom-4 h-24 w-24 bg-blue-500/10 blur-3xl rounded-full" />
                </Card>

                <Card className="relative overflow-hidden border-none bg-gradient-to-br from-purple-500/10 to-purple-500/5 shadow-xl">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Товары на складе</CardTitle>
                        <Package className="h-4 w-4 text-purple-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {loading ? <Loader2 className="h-6 w-6 animate-spin" /> : summary?.total_products.toLocaleString()}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                            Hàng trong kho
                        </p>
                        <Badge variant="secondary" className="mt-2 bg-purple-500/20 text-purple-500 hover:bg-purple-500/30">
                            Синхронизировано
                        </Badge>
                    </CardContent>
                    <div className="absolute -right-4 -bottom-4 h-24 w-24 bg-purple-500/10 blur-3xl rounded-full" />
                </Card>

                <Card className="relative overflow-hidden border-none bg-gradient-to-br from-amber-500/10 to-amber-500/5 shadow-xl">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Аномалии сегодня</CardTitle>
                        <AlertTriangle className="h-4 w-4 text-amber-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {loading ? <Loader2 className="h-6 w-6 animate-spin" /> : summary?.anomalies_today}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                            Bất thường hôm nay
                        </p>
                        <Badge variant="destructive" className="mt-2 bg-amber-500/20 text-amber-500 hover:bg-amber-500/30">
                            {summary?.anomalies_today && summary.anomalies_today > 0 ? 'Требует внимания' : 'Нет аномалий'}
                        </Badge>
                    </CardContent>
                    <div className="absolute -right-4 -bottom-4 h-24 w-24 bg-amber-500/10 blur-3xl rounded-full" />
                </Card>

                <Card className="relative overflow-hidden border-none bg-gradient-to-br from-emerald-500/10 to-emerald-500/5 shadow-xl">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Экономия AI</CardTitle>
                        <TrendingUp className="h-4 w-4 text-emerald-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {loading ? <Loader2 className="h-6 w-6 animate-spin" /> : `${summary?.ai_savings_pct}%`}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                            Tiết kiệm từ AI
                        </p>
                        <Badge variant="secondary" className="mt-2 bg-emerald-500/20 text-emerald-500 hover:bg-emerald-500/30">
                            За месяц
                        </Badge>
                    </CardContent>
                    <div className="absolute -right-4 -bottom-4 h-24 w-24 bg-emerald-500/10 blur-3xl rounded-full" />
                </Card>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
                <Card className="border-border/40 bg-card/50 backdrop-blur-md">
                    <CardHeader>
                        <CardTitle>Последние действия / Hoạt động gần đây</CardTitle>
                        <CardDescription>Лог изменений и уведомлений системы</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {[1, 2, 3].map((i) => (
                                <div key={i} className="flex items-center gap-4 p-3 rounded-lg hover:bg-accent/30 transition-colors">
                                    <div className="h-10 w-10 rounded-full bg-accent flex items-center justify-center">
                                        <Package className="h-5 w-5 text-accent-foreground" />
                                    </div>
                                    <div className="flex-1 space-y-1">
                                        <p className="text-sm font-medium">Синхронизация остатков завершена</p>
                                        <p className="text-xs text-muted-foreground italic">Hoàn tất đồng bộ kho hàng</p>
                                    </div>
                                    <span className="text-xs text-muted-foreground opacity-50">12:30</span>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                <Card className="border-border/40 bg-card/50 backdrop-blur-md">
                    <CardHeader>
                        <CardTitle>Статус iiko / Trạng thái iiko</CardTitle>
                        <CardDescription>Подключение к серверам iiko RESTO</CardDescription>
                    </CardHeader>
                    <CardContent className="flex items-center justify-center p-12">
                        <div className="flex flex-col items-center gap-4">
                            <div className="relative">
                                <div className="h-20 w-20 rounded-full border-4 border-emerald-500/20 animate-pulse" />
                                <div className="absolute inset-0 flex items-center justify-center">
                                    <div className="h-12 w-12 rounded-full bg-emerald-500 flex items-center justify-center text-white font-bold shadow-lg shadow-emerald-500/40">
                                        OK
                                    </div>
                                </div>
                            </div>
                            <div className="text-center">
                                <p className="font-semibold text-emerald-500">Система в норме</p>
                                <p className="text-xs text-muted-foreground italic">Hệ thống đang hoạt động bình thường</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
