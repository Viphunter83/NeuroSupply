"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"
import {
    Settings as SettingsIcon,
    RefreshCcw,
    Save,
    Database,
    FileSpreadsheet,
    ShieldCheck,
    AlertCircle
} from "lucide-react"
import { useState } from "react"

export default function SettingsPage() {
    const [isSyncing, setIsSyncing] = useState(false)

    const handleSync = async (type: string) => {
        setIsSyncing(true)
        // Mocking sync for now as requested in implementation plan
        setTimeout(() => {
            setIsSyncing(false)
            alert(`${type} синхронизация завершена успешно! / Đồng bộ ${type} thành công!`)
        }, 2000)
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1">
                    <h1 className="text-3xl font-bold tracking-tight">Настройки системы / Cài đặt hệ thống</h1>
                    <p className="text-muted-foreground">Управление параметрами расчета и синхронизацией данных</p>
                </div>
                <Button disabled={isSyncing} className="bg-blue-600 hover:bg-blue-500">
                    <Save className="h-4 w-4 mr-2" />
                    Сохранить всё / Lưu tất cả
                </Button>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
                <Card className="bg-card/40 backdrop-blur-md border-border/40">
                    <CardHeader>
                        <div className="flex items-center gap-2">
                            <ShieldCheck className="h-5 w-5 text-blue-500" />
                            <CardTitle>Коэффициенты безопасности</CardTitle>
                        </div>
                        <CardDescription>Настройка запаса прочности для AI-прогноза</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid gap-2">
                            <label className="text-sm font-medium">Safety Stock Factor (0.1 - 2.0)</label>
                            <div className="flex gap-4 items-center">
                                <Input type="number" defaultValue="1.2" step="0.1" className="bg-background/50" />
                                <span className="text-xs text-muted-foreground">+20% к расчетной потребности на случай всплесков</span>
                            </div>
                        </div>
                        <div className="grid gap-2">
                            <label className="text-sm font-medium">Days in Transit (Дни в пути)</label>
                            <Input type="number" defaultValue="1" className="bg-background/50" />
                        </div>
                    </CardContent>
                </Card>

                <Card className="bg-card/40 backdrop-blur-md border-border/40">
                    <CardHeader>
                        <div className="flex items-center gap-2">
                            <RefreshCcw className="h-5 w-5 text-emerald-500" />
                            <CardTitle>Синхронизация данных</CardTitle>
                        </div>
                        <CardDescription>Принудительное обновление из внешних источников</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex items-center justify-between">
                            <div className="space-y-0.5">
                                <div className="text-sm font-medium flex items-center gap-2">
                                    <Database className="h-4 w-4" /> iiko Resto
                                </div>
                                <p className="text-xs text-muted-foreground">Остатки, продажи, техкарты</p>
                            </div>
                            <Button variant="outline" size="sm" onClick={() => handleSync('iiko')} disabled={isSyncing}>
                                Обновить / Cập nhật
                            </Button>
                        </div>
                        <Separator className="opacity-10" />
                        <div className="flex items-center justify-between">
                            <div className="space-y-0.5">
                                <div className="text-sm font-medium flex items-center gap-2">
                                    <FileSpreadsheet className="h-4 w-4" /> Google Sheets
                                </div>
                                <p className="text-xs text-muted-foreground">План продаж, справочник продуктов</p>
                            </div>
                            <Button variant="outline" size="sm" onClick={() => handleSync('GSheets')} disabled={isSyncing}>
                                Обновить / Cập nhật
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            </div>

            <Card className="border-rose-500/20 bg-rose-500/5 backdrop-blur-md">
                <CardHeader>
                    <div className="flex items-center gap-2 text-rose-500">
                        <AlertCircle className="h-5 w-5" />
                        <CardTitle>Опасная зона</CardTitle>
                    </div>
                </CardHeader>
                <CardContent className="flex flex-col md:flex-row justify-between items-center gap-4">
                    <div className="text-sm">
                        <p className="font-bold">Сброс кэша расчетов</p>
                        <p className="text-muted-foreground">Удаляет все текущие черновики и пересчитывает потребность с нуля</p>
                    </div>
                    <Button variant="destructive">Сбросить всё / Reset all</Button>
                </CardContent>
            </Card>
        </div>
    )
}
