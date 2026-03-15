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
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Search, Filter, ArrowDownToLine } from "lucide-react"
import { Button } from "@/components/ui/button"

import { api, StockProduct } from "@/lib/api"
import { useEffect, useState } from "react"
import { Loader2 } from "lucide-react"

export default function StockPage() {
    const [products, setProducts] = useState<StockProduct[]>([])
    const [loading, setLoading] = useState(true)
    const [searchQuery, setSearchQuery] = useState("")

    const handleExport = () => {
        const headers = ["ID", "Name", "Stock", "Unit", "Category"];
        const rows = products.map(p => [
            p.product_id,
            p.product_name,
            p.stock,
            p.unit,
            p.category
        ]);

        const csvContent = "data:text/csv;charset=utf-8,\uFEFF"
            + headers.join(",") + "\n"
            + rows.map(e => e.join(",")).join("\n");

        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `stock_report_${new Date().toISOString().split('T')[0]}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    useEffect(() => {
        const timer = setTimeout(() => {
            setLoading(true)
            api.getProducts(searchQuery)
                .then(setProducts)
                .finally(() => setLoading(false))
        }, 300)
        return () => clearTimeout(timer)
    }, [searchQuery])

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1">
                    <h1 className="text-3xl font-bold tracking-tight">Складской учет / Báo cáo kho</h1>
                    <p className="text-muted-foreground">Просмотр актуальных остатков и номенклатуры</p>
                </div>
                <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" onClick={handleExport}>
                        <ArrowDownToLine className="h-4 w-4 mr-2" />
                        Экспорт / Xuất file
                    </Button>
                    <Button size="sm">
                        Обновить / Cập nhật
                    </Button>
                </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
                <Card className="bg-card/40 backdrop-blur-md border-border/40">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium">Всего позиций</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{loading ? "..." : products.length}</div>
                        <p className="text-xs text-muted-foreground italic">Tổng số mặt hàng</p>
                    </CardContent>
                </Card>
                <Card className="bg-card/40 backdrop-blur-md border-border/40">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium">Критический остаток</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-amber-500">24</div>
                        <p className="text-xs text-muted-foreground italic">Mức tồn kho thấp</p>
                    </CardContent>
                </Card>
                <Card className="bg-card/40 backdrop-blur-md border-border/40">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium">Общая стоимость</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">4.2M ₽</div>
                        <p className="text-xs text-muted-foreground italic">Tổng giá trị</p>
                    </CardContent>
                </Card>
            </div>

            <Card className="border-border/40 bg-card/30 backdrop-blur-xl shadow-2xl overflow-hidden">
                <CardHeader className="bg-accent/5 px-6 py-4">
                    <div className="flex flex-col md:flex-row items-center gap-4 justify-between">
                        <div className="relative w-full md:w-96">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                            <Input
                                placeholder="Поиск товара... / Tìm kiếm..."
                                className="pl-10 bg-background/50 border-border/30"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                            />
                        </div>
                        <div className="flex items-center gap-2 w-full md:w-auto">
                            <Button variant="outline" size="icon" className="shrink-0">
                                <Filter className="h-4 w-4" />
                            </Button>
                            <Badge variant="secondary" className="px-3 py-1">Все категории</Badge>
                        </div>
                    </div>
                </CardHeader>
                <CardContent className="p-0">
                    <Table>
                        <TableHeader className="bg-accent/10">
                            <TableRow className="hover:bg-transparent border-border/20">
                                <TableHead className="w-[300px] font-bold">Наименование / Tên hàng</TableHead>
                                <TableHead className="font-bold">Категория / Danh mục</TableHead>
                                <TableHead className="text-right font-bold">Остаток / Tồn kho</TableHead>
                                <TableHead className="text-center font-bold">Статус / Trạng thái</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {loading ? (
                                <TableRow>
                                    <TableCell colSpan={4} className="text-center py-10">
                                        <Loader2 className="h-10 w-10 animate-spin mx-auto text-muted-foreground" />
                                    </TableCell>
                                </TableRow>
                            ) : products.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={4} className="text-center py-10 text-muted-foreground">
                                        Ничего не найдено / Không tìm thấy
                                    </TableCell>
                                </TableRow>
                            ) : products.map((p) => (
                                <TableRow key={p.product_id} className="hover:bg-accent/20 transition-colors border-border/10 cursor-pointer">
                                    <TableCell className="font-medium">
                                        <div className="flex flex-col">
                                            <span className="text-foreground">{p.product_name}</span>
                                            <span className="text-xs text-muted-foreground italic font-normal">{p.product_name_vn}</span>
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        <Badge variant="outline" className="font-normal border-border/50 bg-background/20">
                                            {p.category}
                                        </Badge>
                                    </TableCell>
                                    <TableCell className="text-right">
                                        <div className="flex flex-col items-end">
                                            <span className="text-sm font-bold">{p.stock || 0} {p.unit}</span>
                                        </div>
                                    </TableCell>
                                    <TableCell className="text-center">
                                        <Badge className="bg-emerald-500/20 text-emerald-500 border-none">
                                            В норме / Ok
                                        </Badge>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    )
}
