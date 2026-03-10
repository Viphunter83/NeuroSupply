"use client"

import * as React from "react"
import Link from "next/link"
import {
    LayoutDashboard,
    ShoppingCart,
    Package,
    History,
    Settings,
    AlertTriangle,
    ChevronRight,
    Users,
} from "lucide-react"

import {
    Sidebar,
    SidebarContent,
    SidebarFooter,
    SidebarHeader,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
    SidebarGroup,
    SidebarGroupLabel,
    SidebarGroupContent,
} from "@/components/ui/sidebar"

// Menu items.
const items = [
    {
        title: "Главная / Trang chủ",
        url: "/dashboard",
        icon: LayoutDashboard,
    },
    {
        title: "Заявки / Đơn hàng",
        url: "/dashboard/orders",
        icon: ShoppingCart,
    },
    {
        title: "Склад / Kho hàng",
        url: "/dashboard/stock",
        icon: Package,
    },
    {
        title: "Аномалии / Bất thường",
        url: "/dashboard/anomalies",
        icon: AlertTriangle,
    },
    {
        title: "История / Lịch sử",
        url: "/dashboard/history",
        icon: History,
    },
    {
        title: "Персонал / Nhân viên",
        url: "/dashboard/staff",
        icon: Users,
    },
    {
        title: "Настройки / Cài đặt",
        url: "/dashboard/settings",
        icon: Settings,
    },
]

import { getRestaurantId } from "@/lib/api"

export function AppSidebar() {
    const restaurantId = getRestaurantId()

    return (
        <Sidebar variant="floating" collapsible="icon">
            <SidebarHeader className="p-4">
                <div className="flex items-center gap-2 px-2 py-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                        <LayoutDashboard className="h-5 w-5" />
                    </div>
                    <div className="flex flex-col gap-0.5 leading-none">
                        <span className="font-semibold text-lg tracking-tight">NeuroSupply</span>
                        <span className="text-xs text-muted-foreground opacity-70">v1.2.0-beta</span>
                    </div>
                </div>
            </SidebarHeader>
            <SidebarContent>
                <SidebarGroup>
                    <SidebarGroupLabel>Управление / Quản lý</SidebarGroupLabel>
                    <SidebarGroupContent>
                        <SidebarMenu>
                            {items.map((item) => {
                                const Icon = item.icon
                                const url = restaurantId
                                    ? `${item.url}?restaurant_id=${restaurantId}`
                                    : item.url

                                return (
                                    <SidebarMenuItem key={item.title}>
                                        <SidebarMenuButton
                                            render={<Link href={url} />}
                                            className="hover:bg-accent/50 transition-colors"
                                        >
                                            <Icon />
                                            <span className="font-medium">{item.title}</span>
                                        </SidebarMenuButton>
                                    </SidebarMenuItem>
                                )
                            })}
                        </SidebarMenu>
                    </SidebarGroupContent>
                </SidebarGroup>
            </SidebarContent>
            <SidebarFooter className="p-4 border-t border-border/50">
                <div className="flex items-center gap-3 px-2">
                    <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500" />
                    <div className="flex flex-col">
                        <span className="text-sm font-medium">Администратор</span>
                        <span className="text-xs text-muted-foreground italic">Admin / Quản trị viên</span>
                    </div>
                </div>
            </SidebarFooter>
        </Sidebar>
    )
}
