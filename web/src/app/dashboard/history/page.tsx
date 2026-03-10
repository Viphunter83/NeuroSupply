"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
    Clock,
    CheckCircle2,
    AlertCircle,
    RefreshCcw,
    User,
    ChevronRight,
    ArrowUpRight
} from "lucide-react"

export default function HistoryPage() {
    // Mock events for now
    const events = [
        {
            id: 1,
            type: "sync",
            title: "Успешная синхронизация с iiko",
            description: "Обновлено 1,240 позиций остатков",
            time: "10:00 AM",
            status: "success",
            user: "System AI"
        },
        {
            id: 2,
            type: "order",
            title: "Заявка подтверждена поваром",
            description: "Точка: Landmark 81. Позиций: 45",
            time: "09:30 AM",
            status: "success",
            user: "Nguyen Van A"
        },
        {
            id: 3,
            type: "anomaly",
            title: "Обнаружена критическая аномалия",
            description: "Мясо говядина: отклонение +150% от прогноза",
            time: "09:15 AM",
            status: "warning",
            user: "AI Monitor"
        },
        {
            id: 4,
            type: "config",
            title: "Изменение настроек",
            description: "Safety Stock Factor изменен с 1.1 на 1.2",
            time: "Вчера, 18:45",
            status: "info",
            user: "Manager"
        }
    ]

    const getIcon = (type: string) => {
        switch (type) {
            case 'sync': return <RefreshCcw className="h-4 w-4 text-blue-500" />
            case 'order': return <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            case 'anomaly': return <AlertCircle className="h-4 w-4 text-amber-500" />
            default: return <Clock className="h-4 w-4 text-zinc-400" />
        }
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1">
                    <h1 className="text-3xl font-bold tracking-tight">История событий / Nhật ký hoạt động</h1>
                    <p className="text-muted-foreground">Лента активности системы и действий пользователей</p>
                </div>
            </div>

            <div className="grid gap-4">
                {events.map((event) => (
                    <Card key={event.id} className="bg-card/40 backdrop-blur-md border-border/40 hover:bg-accent/5 transition-all cursor-pointer group">
                        <CardContent className="p-4 flex items-center gap-4">
                            <div className="h-10 w-10 rounded-full bg-accent/10 flex items-center justify-center shrink-0">
                                {getIcon(event.type)}
                            </div>
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-0.5">
                                    <p className="font-semibold text-sm truncate">{event.title}</p>
                                    <Badge variant="outline" className="text-[10px] h-4">
                                        {event.type.toUpperCase()}
                                    </Badge>
                                </div>
                                <p className="text-xs text-muted-foreground truncate">{event.description}</p>
                            </div>
                            <div className="hidden md:flex flex-col items-end gap-1 px-4 border-l border-border/10 shrink-0">
                                <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
                                    <User className="h-3 w-3" /> {event.user}
                                </div>
                                <div className="text-[10px] font-mono opacity-50">{event.time}</div>
                            </div>
                            <div className="shrink-0 opacity-20 group-hover:opacity-100 transition-opacity">
                                <ChevronRight className="h-5 w-5" />
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            <div className="flex justify-center mt-8">
                <p className="text-xs text-muted-foreground flex items-center gap-1 cursor-pointer hover:text-foreground">
                    Загрузить более ранние события <ArrowUpRight className="h-3 w-3" />
                </p>
            </div>
        </div>
    )
}
