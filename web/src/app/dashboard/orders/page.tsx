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
import { CheckCircle2, Clock, Send, MessageCircle } from "lucide-react"

import { api } from "@/lib/api"
import { useEffect, useState } from "react"
import { Loader2 } from "lucide-react"

export default function OrdersPage() {
    const [orders, setOrders] = useState<any[]>([])
    const [loading, setLoading] = useState(true)

    const fetchOrders = () => {
        setLoading(true)
        api.listOrders() // uses getRestaurantId() internally now
            .then(setOrders)
            .finally(() => setLoading(false))
    }

    useEffect(() => {
        fetchOrders()
    }, [])

    const handleApprove = async (id: string) => {
        try {
            await api.approveOrder(id)
            fetchOrders()
        } catch (err) {
            alert('Ошибка при одобрении / Lỗi khi duyệt')
        }
    }

    const handleExport = (id: string) => {
        window.open(api.getExportUrl(id), '_blank')
    }

    const handleBulkExport = () => {
        const headers = ["ID", "Restaurant", "Status", "Date", "Items Count"];
        const rows = orders.map(o => [
            o.id,
            o.restaurant_name,
            o.status,
            new Date(o.created_at).toLocaleString(),
            o.items_count
        ]);

        const csvContent = "data:text/csv;charset=utf-8,\uFEFF"
            + headers.join(",") + "\n"
            + rows.map(e => e.join(",")).join("\n");

        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `orders_report_${new Date().toISOString().split('T')[0]}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1">
                    <h1 className="text-3xl font-bold tracking-tight">Заявки и Закупы / Đơn hàng & Thu mua</h1>
                    <p className="text-muted-foreground">Управление расчетами и подтверждение заказов от поваров</p>
                </div>
                <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" onClick={handleBulkExport}>
                        <Send className="h-4 w-4 mr-2" />
                        Экспорт / Xuất file
                    </Button>
                    <Button size="sm">
                        Создать вручную / Tạo thủ công
                    </Button>
                </div>
            </div>

            <div className="grid gap-6">
                {loading ? (
                    <Card className="p-20 flex flex-col items-center gap-4">
                        <Loader2 className="h-10 w-10 animate-spin text-muted-foreground" />
                        <p>Загрузка заказов... / Đang tải đơn hàng...</p>
                    </Card>
                ) : orders.length === 0 ? (
                    <Card className="p-20 text-center text-muted-foreground">
                        Нет активных заявок / Không có đơn hàng nào
                    </Card>
                ) : orders.map((order) => (
                    <Card key={order.id} className="border-border/40 bg-card/40 backdrop-blur-md shadow-lg hover:shadow-xl transition-shadow overflow-hidden">
                        <CardHeader className="flex flex-row items-center justify-between bg-accent/5 p-6 border-b border-border/10">
                            <div className="space-y-1">
                                <div className="flex items-center gap-3">
                                    <CardTitle className="text-xl font-bold">{order.restaurant_name}</CardTitle>
                                    <Badge
                                        variant={order.status === "approved_by_manager" ? "default" : "secondary"}
                                        className={order.status === "approved_by_manager" ? "bg-emerald-500 text-white" : "bg-amber-500/20 text-amber-500"}
                                    >
                                        {order.status === "approved_by_manager" ? "Одобрено" : "Ожидает"}
                                    </Badge>
                                </div>
                                <CardDescription className="flex items-center gap-2">
                                    <Clock className="h-3 w-3" /> {new Date(order.created_at).toLocaleTimeString()} | ID: {order.id.slice(0, 8)}
                                </CardDescription>
                            </div>
                            <div className="flex gap-2">
                                {order.status === "verified_by_cook" && (
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        className="text-emerald-500 hover:text-emerald-400 hover:bg-emerald-500/10"
                                        onClick={() => handleApprove(order.id)}
                                    >
                                        <CheckCircle2 className="h-4 w-4 mr-2" /> Одобрить / Duyệt
                                    </Button>
                                )}
                                <Button size="sm" variant="outline" onClick={() => handleExport(order.id)}>Excel</Button>
                                <Button size="sm" variant="outline">Подробнее / Chi tiết</Button>
                            </div>
                        </CardHeader>
                        <CardContent className="p-0">
                            <Table>
                                <TableHeader className="bg-accent/5">
                                    <TableRow className="hover:bg-transparent border-none text-[10px] uppercase tracking-wider opacity-60">
                                        <TableHead className="pl-6">Товар / Hàng</TableHead>
                                        <TableHead>Остаток / Tồn</TableHead>
                                        <TableHead>План / Kế hoạch</TableHead>
                                        <TableHead className="text-right pr-6 font-bold text-foreground opacity-100">Закуп / Mua</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {order.items?.slice(0, 3).map((item: any) => (
                                        <TableRow key={item.product_id} className="border-border/5">
                                            <TableCell className="pl-6 py-4">
                                                <div className="flex flex-col">
                                                    <span className="font-medium">{item.product_name}</span>
                                                    <span className="text-xs text-muted-foreground italic">{item.product_name_vn}</span>
                                                </div>
                                            </TableCell>
                                            <TableCell>{item.stock} {item.unit}</TableCell>
                                            <TableCell>{item.predicted_usage} {item.unit}</TableCell>
                                            <TableCell className="text-right pr-6">
                                                <Badge className="bg-blue-500 hover:bg-blue-600 text-white font-bold px-3 py-1">
                                                    {item.quantity} {item.unit}
                                                </Badge>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </CardContent>
                        <div className="bg-accent/5 p-4 flex justify-between items-center text-xs text-muted-foreground border-t border-border/10">
                            <span>Итого позиций: {order.items_count}</span>
                            <span className="font-bold text-foreground">Статус: {order.status}</span>
                        </div>
                    </Card>
                ))}
            </div>

            <div className="flex justify-center py-6">
                <Button variant="secondary" className="bg-accent/50 hover:bg-accent transition-colors gap-2">
                    Показать все заявки / Xem tất cả
                </Button>
            </div>
        </div>
    )
}
