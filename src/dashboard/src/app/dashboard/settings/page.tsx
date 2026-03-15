"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Separator } from "@/components/ui/separator"
import {
    Settings as SettingsIcon,
    RefreshCcw,
    Save,
    Database,
    ShieldCheck,
    AlertCircle,
    Loader2
} from "lucide-react"
import { useState, useEffect } from "react"
import { api, getRestaurantId } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

export default function SettingsPage() {
    const [isSyncing, setIsSyncing] = useState(false)
    const [isSaving, setIsSaving] = useState(false)
    const [isLoading, setIsLoading] = useState(true)
    const [settings, setSettings] = useState({
        safety_stock_ratio: 1.2,
        days_in_transit: 1
    })
    const { toast } = useToast()
    const restaurantId = getRestaurantId()

    useEffect(() => {
        if (restaurantId) {
            loadSettings()
        }
    }, [restaurantId])

    const loadSettings = async () => {
        try {
            setIsLoading(true)
            const data = await api.getRestaurantSettings(restaurantId!)
            if (data.settings) {
                setSettings({
                    safety_stock_ratio: data.settings.safety_stock_ratio || 1.2,
                    days_in_transit: data.settings.days_in_transit || 1
                })
            }
        } catch (error) {
            toast({
                title: "Ошибка / Lỗi",
                description: "Не удалось загрузить настройки / Không thể tải cài đặt",
                variant: "destructive"
            })
        } finally {
            setIsLoading(false)
        }
    }

    const handleSave = async () => {
        if (!restaurantId) return
        try {
            setIsSaving(true)
            await api.updateRestaurantSettings(restaurantId, settings)
            toast({
                title: "Успешно / Thành công",
                description: "Настройки сохранены / Cài đặt đã được lưu",
            })
        } catch (error) {
            toast({
                title: "Ошибка / Lỗi",
                description: "Не удалось сохранить настройки / Không thể lưu cài đặt",
                variant: "destructive"
            })
        } finally {
            setIsSaving(false)
        }
    }

    const handleSync = async () => {
        if (!restaurantId) return
        try {
            setIsSyncing(true)
            await api.syncIikoData(restaurantId)
            toast({
                title: "Успешно / Thành công",
                description: "Синхронизация с iiko завершена / Đồng bộ iiko hoàn tất",
            })
        } catch (error) {
            toast({
                title: "Ошибка / Lỗi",
                description: "Синхронизация не удалась / Đồng bộ thất bại",
                variant: "destructive"
            })
        } finally {
            setIsSyncing(false)
        }
    }

    if (isLoading) {
        return (
            <div className="flex h-[400px] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        )
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1">
                    <h1 className="text-3xl font-bold tracking-tight">Настройки ресторана / Cài đặt nhà hàng</h1>
                    <p className="text-muted-foreground">Управление параметрами расчета и синхронизацией данных iiko</p>
                </div>
                <Button 
                    disabled={isSaving || isSyncing} 
                    className="bg-blue-600 hover:bg-blue-500"
                    onClick={handleSave}
                >
                    {isSaving ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
                    Сохранить / Lưu
                </Button>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
                <Card className="bg-card/40 backdrop-blur-md border-border/40">
                    <CardHeader>
                        <div className="flex items-center gap-2">
                            <ShieldCheck className="h-5 w-5 text-blue-500" />
                            <CardTitle>Параметры запаса</CardTitle>
                        </div>
                        <CardDescription>Настройка страхового запаса и логистики</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid gap-2">
                            <label className="text-sm font-medium">Safety Stock Factor (1.0 - 2.0)</label>
                            <div className="grid gap-1">
                                <Input 
                                    type="number" 
                                    value={settings.safety_stock_ratio} 
                                    onChange={(e) => setSettings({...settings, safety_stock_ratio: parseFloat(e.target.value)})}
                                    step="0.05" 
                                    className="bg-background/50" 
                                />
                                <span className="text-[10px] text-muted-foreground">Коэффициент умножения прогноза (1.2 = +20% запаса)</span>
                            </div>
                        </div>
                        <div className="grid gap-2">
                            <label className="text-sm font-medium">Days in Transit (Дни в пути)</label>
                            <Input 
                                type="number" 
                                value={settings.days_in_transit} 
                                onChange={(e) => setSettings({...settings, days_in_transit: parseInt(e.target.value)})}
                                className="bg-background/50" 
                            />
                        </div>
                    </CardContent>
                </Card>

                <Card className="bg-card/40 backdrop-blur-md border-border/40">
                    <CardHeader>
                        <div className="flex items-center gap-2">
                            <RefreshCcw className="h-5 w-5 text-emerald-500" />
                            <CardTitle>Интеграция iiko</CardTitle>
                        </div>
                        <CardDescription>Прямое обновление данных из iiko Cloud/Resto</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex items-center justify-between">
                            <div className="space-y-0.5">
                                <div className="text-sm font-medium flex items-center gap-2">
                                    <Database className="h-4 w-4" /> iiko Cloud & Resto
                                </div>
                                <p className="text-xs text-muted-foreground">Остатки на складах и техкарты блюд</p>
                            </div>
                            <Button variant="outline" size="sm" onClick={handleSync} disabled={isSyncing || isSaving}>
                                {isSyncing ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <RefreshCcw className="h-4 w-4 mr-2" />}
                                Синхронизировать / Đồng bộ
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            </div>

            <Card className="border-rose-500/20 bg-rose-500/5 backdrop-blur-md">
                <CardHeader>
                    <div className="flex items-center gap-2 text-rose-500">
                        <AlertCircle className="h-5 w-5" />
                        <CardTitle>Google Sheets</CardTitle>
                    </div>
                    <CardDescription className="text-rose-400/60 font-medium">Система переходит на Pure Web. Использование таблиц ограничено.</CardDescription>
                </CardHeader>
                <CardContent>
                    <p className="text-sm text-muted-foreground">
                        Настройки в Google Sheets больше не приоритетны. Используйте эту страницу для управления параметрами.
                    </p>
                </CardContent>
            </Card>
        </div>
    )
}
