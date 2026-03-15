"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Users, Shield, MapPin, Loader2 } from "lucide-react"

export default function StaffPage() {
    const [users, setUsers] = useState<any[]>([])
    const [restaurants, setRestaurants] = useState<any[]>([])
    const [loading, setLoading] = useState(true)

    const fetchData = async () => {
        try {
            const [usersData, restsData] = await Promise.all([
                api.listUsers(),
                api.listRestaurants()
            ])
            setUsers(usersData)
            setRestaurants(restsData)
        } catch (error) {
            console.error("Failed to fetch staff data", error)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => { fetchData() }, [])

    const handleUpdateUser = async (userId: string, data: any) => {
        try {
            await api.updateUser(userId, data)
            fetchData() // Refresh
        } catch (error) {
            alert("Ошибка при обновлении пользователя")
        }
    }

    if (loading) {
        return (
            <div className="flex h-[400px] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        )
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-col gap-2">
                <h1 className="text-3xl font-bold tracking-tight">Персонал / Nhân viên</h1>
                <p className="text-muted-foreground">Управление ролями и привязкой к ресторанам.</p>
            </div>

            <Card className="border-none shadow-xl bg-card/50 backdrop-blur-md">
                <CardHeader>
                    <div className="flex items-center gap-2">
                        <Users className="h-5 w-5 text-primary" />
                        <CardTitle>Список пользователей</CardTitle>
                    </div>
                    <CardDescription>Все пользователи, зарегистрированные в Web-платформе</CardDescription>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Аккаунт / Tài khoản</TableHead>
                                <TableHead>Роль / Vai trò</TableHead>
                                <TableHead>Ресторан / Nhà hàng</TableHead>
                                <TableHead className="text-right">ID</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {users.map((user) => (
                                <TableRow key={user.id}>
                                    <TableCell className="font-medium text-xs">
                                        {user.email || (user.telegram_id ? `TG: ${user.telegram_id}` : "Unknown")}
                                    </TableCell>
                                    <TableCell>
                                        <Select
                                            defaultValue={user.role}
                                            onValueChange={(val: string) => handleUpdateUser(user.id, { role: val })}
                                        >
                                            <SelectTrigger className="w-[140px] h-8 text-xs bg-background/50">
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="cook">Повар (Cook)</SelectItem>
                                                <SelectItem value="manager">Менеджер (Manager)</SelectItem>
                                                <SelectItem value="admin">Админ (Admin)</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </TableCell>
                                    <TableCell>
                                        <Select
                                            defaultValue={user.restaurant_id || "none"}
                                            onValueChange={(val: string) => handleUpdateUser(user.id, { linked_restaurant_id: val === "none" ? null : val })}
                                        >
                                            <SelectTrigger className="w-[200px] h-8 text-xs bg-background/50">
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="none">Не привязан</SelectItem>
                                                {restaurants.map((r) => (
                                                    <SelectItem key={r.id} value={r.id}>{r.name}</SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                    </TableCell>
                                    <TableCell className="text-right text-[10px] text-muted-foreground font-mono">
                                        {user.id.slice(0, 8)}
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            <div className="grid gap-4 md:grid-cols-2">
                <Card className="border-none bg-blue-500/5">
                    <CardHeader className="pb-2">
                        <div className="flex items-center gap-2">
                            <Shield className="h-4 w-4 text-blue-500" />
                            <CardTitle className="text-sm">Как добавить сотрудника?</CardTitle>
                        </div>
                    </CardHeader>
                    <CardContent className="text-xs text-muted-foreground space-y-2">
                        <p>1. Попросите сотрудника зарегистрироваться на сайте.</p>
                        <p>2. Он появится в этом списке автоматически после входа.</p>
                        <p>3. Выберите нужную роль и привяжите к ресторану здесь.</p>
                    </CardContent>
                </Card>
                <Card className="border-none bg-emerald-500/5">
                    <CardHeader className="pb-2">
                        <div className="flex items-center gap-2">
                            <MapPin className="h-4 w-4 text-emerald-500" />
                            <CardTitle className="text-sm">Что дает привязка?</CardTitle>
                        </div>
                    </CardHeader>
                    <CardContent className="text-xs text-muted-foreground space-y-2">
                        <p>Повар будет видеть заказы только своего ресторана.</p>
                        <p>Менеджер сможет переключаться между доступными точками.</p>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
