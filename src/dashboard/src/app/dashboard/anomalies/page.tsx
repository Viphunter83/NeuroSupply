"use client"

import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { AlertTriangle, CheckCircle2, Info, TrendingDown, TrendingUp, Filter, Download } from "lucide-react"

import { api } from "@/lib/api"
import { useEffect, useState } from "react"
import { Loader2 } from "lucide-react"

export default function AnomaliesPage() {
    const [anomalies, setAnomalies] = useState<any[]>([])
    const [loading, setLoading] = useState(true)

    const fetchAnomalies = () => {
        setLoading(true)
        api.listAnomalies()
            .then(setAnomalies)
            .catch(err => console.error(err))
            .finally(() => setLoading(false))
    }

    useEffect(() => {
        fetchAnomalies()
    }, [])

    const handleApprove = async (id: string) => {
        try {
            await api.approveAnomaly(id)
            fetchAnomalies()
        } catch (err) {
            alert('Ошибка при одобрении / Lỗi khi duyệt')
        }
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1">
                    <h1 className="text-3xl font-bold tracking-tight">Журнал аномалий / Nhật ký bất thường</h1>
                    <p className="text-muted-foreground">Анализ расхождений между расчетом AI и заказом повара</p>
                </div>
                <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm">
                        <Filter className="h-4 w-4 mr-2" />
                        Фильтр / Lọc
                    </Button>
                    <Button variant="outline" size="sm">
                        <Download className="h-4 w-4 mr-2" />
                        Экспорт / Xuất
                    </Button>
                </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card className="bg-card/40 backdrop-blur-md border-border/40">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Всего аномалий</CardTitle>
                        <AlertTriangle className="h-4 w-4 text-amber-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{anomalies.length}</div>
                        <p className="text-xs text-muted-foreground">За последние 7 дней</p>
                    </CardContent>
                </Card>
                <Card className="bg-card/40 backdrop-blur-md border-border/40">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Крупные отклонения</CardTitle>
                        <TrendingUp className="h-4 w-4 text-rose-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {anomalies.filter(a => Math.abs(a.diff / a.auto_qty) > 0.5).length}
                        </div>
                        <p className="text-xs text-muted-foreground">{">"} 50% от прогноза</p>
                    </CardContent>
                </Card>
            </div>

            <Card className="border-border/40 bg-card/40 backdrop-blur-md">
                <CardHeader>
                    <CardTitle>Список отклонений</CardTitle>
                    <CardDescription>Сравнение прогноза системы и ручного ввода повара</CardDescription>
                </CardHeader>
                <CardContent className="p-0">
                    {loading ? (
                        <div className="p-20 flex flex-col items-center gap-4">
                            <Loader2 className="h-10 w-10 animate-spin text-muted-foreground" />
                            <p>Загрузка данных... / Đang tải dữ liệu...</p>
                        </div>
                    ) : anomalies.length === 0 ? (
                        <div className="p-20 text-center text-muted-foreground">
                            Аномалий не обнаружено / Không tìm thấy bất thường
                        </div>
                    ) : (
                        <Table>
                            <TableHeader>
                                <TableRow className="hover:bg-transparent border-border/10">
                                    <TableHead className="w-[250px] pl-6">Товар / Hàng</TableHead>
                                    <TableHead>Расчет AI / AI tính</TableHead>
                                    <TableHead>Повар / Đầu bếp</TableHead>
                                    <TableHead>Разница / Chênh lệch</TableHead>
                                    <TableHead className="w-[300px]">Причина / Lý do</TableHead>
                                    <TableHead className="text-right pr-6">Действие</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {anomalies.map((anomaly) => {
                                    const diffPct = (anomaly.diff / anomaly.auto_qty) * 100
                                    const isHigh = Math.abs(diffPct) > 30

                                    return (
                                        <TableRow key={anomaly.id} className="border-border/5 hover:bg-accent/5 transition-colors">
                                            <TableCell className="pl-6 py-4">
                                                <div className="flex flex-col">
                                                    <span className="font-medium">{anomaly.product_name}</span>
                                                    <span className="text-xs text-muted-foreground italic">{anomaly.product_name_vn}</span>
                                                </div>
                                            </TableCell>
                                            <TableCell className="font-mono">{anomaly.auto_qty} {anomaly.unit}</TableCell>
                                            <TableCell className="font-mono font-bold">{anomaly.manual_qty} {anomaly.unit}</TableCell>
                                            <TableCell>
                                                <div className="flex items-center gap-2">
                                                    {anomaly.diff > 0 ? (
                                                        <TrendingUp className="h-3 w-3 text-rose-500" />
                                                    ) : (
                                                        <TrendingDown className="h-3 w-3 text-emerald-500" />
                                                    )}
                                                    <Badge variant={isHigh ? "destructive" : "secondary"} className="font-mono">
                                                        {anomaly.diff > 0 ? "+" : ""}{anomaly.diff} ({Math.round(diffPct)}%)
                                                    </Badge>
                                                </div>
                                            </TableCell>
                                            <TableCell>
                                                <div className="flex items-start gap-2 max-w-[280px]">
                                                    <Info className="h-4 w-4 mt-0.5 text-muted-foreground shrink-0" />
                                                    <span className="text-sm leading-tight text-muted-foreground">
                                                        {anomaly.reason || "Без комментария / Không có chú thích"}
                                                    </span>
                                                </div>
                                            </TableCell>
                                            <TableCell className="text-right pr-6">
                                                {anomaly.order_status === "verified_by_cook" ? (
                                                    <Button
                                                        size="sm"
                                                        variant="ghost"
                                                        className="text-emerald-500 hover:text-emerald-400 hover:bg-emerald-500/10"
                                                        onClick={() => handleApprove(anomaly.id)}
                                                    >
                                                        <CheckCircle2 className="h-4 w-4 mr-2" />
                                                        Одобрить
                                                    </Button>
                                                ) : (
                                                    <Badge variant="outline" className="opacity-50">
                                                        {anomaly.order_status === "approved_by_manager" ? "Одобрено" : anomaly.order_status}
                                                    </Badge>
                                                )}
                                            </TableCell>
                                        </TableRow>
                                    )
                                })}
                            </TableBody>
                        </Table>
                    )}
                </CardContent>
            </Card>
        </div>
    )
}
