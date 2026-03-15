
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

export interface DashboardSummary {
    active_orders: number;
    total_products: number;
    anomalies_today: number;
    ai_savings_pct: number;
    iiko_status: string;
}

export interface StockProduct {
    product_id: string;
    product_name: string;
    product_name_vn: string;
    unit: string;
    category: string;
    stock?: number;
}

export interface Order {
    id: string;
    restaurant_id: string;
    status: string;
    created_at: string;
    items: any[];
    total_amount?: string;
}

export const getRestaurantId = (): string | null => {
    if (typeof window === 'undefined') return null;
    const urlParams = new URLSearchParams(window.location.search);
    const id = urlParams.get('restaurant_id');
    if (id) {
        localStorage.setItem('last_restaurant_id', id);
        return id;
    }
    return localStorage.getItem('last_restaurant_id');
};

const fetchWithAuth = async (url: string, options: RequestInit = {}) => {
    const headers = new Headers(options.headers);

    // Check for auth token in localStorage (aligned with Mini App)
    if (typeof window !== 'undefined') {
        const session = localStorage.getItem('neurosupply_auth_session');
        if (session) {
            const { access_token } = JSON.parse(session);
            headers.set('Authorization', `Bearer ${access_token}`);
        }
    } else if (process.env.NODE_ENV === 'development') {
        // Fallback for local testing
        headers.set('X-Dev-User-Id', '1');
    }

    return fetch(url, { ...options, headers });
};

export const api = {
    async getMe(): Promise<any> {
        const url = `${API_BASE_URL}/api/v1/auth/me`;
        const res = await fetchWithAuth(url);
        if (!res.ok) throw new Error('Failed to fetch user info');
        return res.json();
    },

    async getSummary(restaurantId?: string): Promise<DashboardSummary> {
        const id = restaurantId || getRestaurantId();
        const url = new URL(`${API_BASE_URL}/api/v1/analytics/summary`, window.location.origin);
        if (id) url.searchParams.append('restaurant_id', id);

        const res = await fetchWithAuth(url.toString());
        if (!res.ok) throw new Error('Failed to fetch summary');
        return res.json();
    },

    async getProducts(query: string = '', restaurantId?: string): Promise<StockProduct[]> {
        const id = restaurantId || getRestaurantId();
        const url = new URL(`${API_BASE_URL}/api/v1/products/extra`, window.location.origin);
        if (query) url.searchParams.append('q', query);
        if (id) url.searchParams.append('restaurant_id', id);

        const res = await fetchWithAuth(url.toString());
        if (!res.ok) throw new Error('Failed to fetch products');
        return res.json();
    },

    async getLatestOrder(restaurantId?: string): Promise<Order> {
        const id = restaurantId || getRestaurantId();
        const url = new URL(`${API_BASE_URL}/api/v1/orders/latest`, window.location.origin);
        if (id) url.searchParams.append('restaurant_id', id);

        const res = await fetchWithAuth(url.toString());
        if (!res.ok) throw new Error('Failed to fetch latest order');
        return res.json();
    },

    async listOrders(restaurantId?: string): Promise<any[]> {
        const id = restaurantId || getRestaurantId();
        const url = new URL(`${API_BASE_URL}/api/v1/orders/`, window.location.origin);
        if (id) url.searchParams.append('restaurant_id', id);

        const res = await fetchWithAuth(url.toString());
        if (!res.ok) throw new Error('Failed to fetch orders');
        return res.json();
    },

    async listAnomalies(restaurantId?: string): Promise<any[]> {
        const id = restaurantId || getRestaurantId();
        const url = new URL(`${API_BASE_URL}/api/v1/anomalies/`, window.location.origin);
        if (id) url.searchParams.append('restaurant_id', id);

        const res = await fetchWithAuth(url.toString());
        if (!res.ok) throw new Error('Failed to fetch anomalies');
        return res.json();
    },

    async approveAnomaly(anomalyId: string): Promise<void> {
        const url = `${API_BASE_URL}/api/v1/anomalies/${anomalyId}/approve`;
        const res = await fetchWithAuth(url, { method: 'POST' });
        if (!res.ok) throw new Error('Failed to approve anomaly');
    },

    async approveOrder(orderId: string): Promise<void> {
        const url = `${API_BASE_URL}/api/v1/orders/${orderId}/approve`;
        const res = await fetchWithAuth(url, { method: 'POST' });
        if (!res.ok) throw new Error('Failed to approve order');
    },

    async listUsers(): Promise<any[]> {
        const url = `${API_BASE_URL}/api/v1/auth/users`;
        const res = await fetchWithAuth(url);
        if (!res.ok) throw new Error('Failed to fetch users');
        return res.json();
    },

    async updateUser(userId: string, data: any): Promise<void> {
        const url = `${API_BASE_URL}/api/v1/auth/users/${userId}`;
        const res = await fetchWithAuth(url, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error('Failed to update user');
    },

    async listRestaurants(): Promise<any[]> {
        const url = `${API_BASE_URL}/api/v1/analytics/restaurants`;
        const res = await fetchWithAuth(url);
        if (!res.ok) throw new Error('Failed to fetch restaurants');
        return res.json();
    },

    async downloadOrderExcel(orderId: string): Promise<void> {
        const url = `${API_BASE_URL}/api/v1/orders/${orderId}/export/excel`;
        const res = await fetchWithAuth(url);
        if (!res.ok) throw new Error('Failed to download Excel');
        
        const blob = await res.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = `Order_${orderId.slice(0, 8)}.xlsx`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(downloadUrl);
    },

    async getRestaurantSettings(restaurantId: string): Promise<any> {
        const url = `${API_BASE_URL}/api/v1/restaurants/${restaurantId}`;
        const res = await fetchWithAuth(url);
        if (!res.ok) throw new Error('Failed to fetch restaurant settings');
        return res.json();
    },

    async updateRestaurantSettings(restaurantId: string, settings: any): Promise<any> {
        const url = `${API_BASE_URL}/api/v1/restaurants/${restaurantId}/settings`;
        const res = await fetchWithAuth(url, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ settings })
        });
        if (!res.ok) throw new Error('Failed to update settings');
        return res.json();
    },

    async syncIikoData(restaurantId: string): Promise<any> {
        const url = `${API_BASE_URL}/api/v1/restaurants/${restaurantId}/sync`;
        const res = await fetchWithAuth(url, { method: 'POST' });
        if (!res.ok) throw new Error('Sync failed');
        return res.json();
    }
};
