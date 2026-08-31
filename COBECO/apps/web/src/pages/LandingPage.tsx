import { useState, useEffect } from 'react';
import { apiService } from '../services/api';

interface Testimonial {
  id: string;
  authorName: string;
  content: string;
}

interface Retailer {
  id: string;
  name: string;
  slug: string;
  websiteUrl: string;
}

/**
 * Padrão de busca de cada varejista. Sem catálogo próprio de exemplo, o link
 * leva à busca do produto no site do lojista — mesmo destino que a cotação real
 * usa quando o provider não devolve um permalink.
 */
const SEARCH_PATTERNS: Record<string, (query: string) => string> = {
  amazon: (q) => `https://www.amazon.com.br/s?k=${encodeURIComponent(q)}`,
  'mercado-livre': (q) => `https://lista.mercadolivre.com.br/${encodeURIComponent(q)}`,
  shopee: (q) => `https://shopee.com.br/search?keyword=${encodeURIComponent(q)}`,
  'magazine-luiza': (q) => `https://www.magazineluiza.com.br/busca/${encodeURIComponent(q)}`,
};

function buildProductUrl(slug: string, query: string, websiteUrl?: string): string {
  const pattern = SEARCH_PATTERNS[slug];
  if (pattern) return pattern(query);
  return websiteUrl || '#';
}

export function LandingPage() {
  const [testimonials, setTestimonials] = useState<Testimonial[]>([]);
  const [retailers, setRetailers] = useState<Retailer[]>([]);
  const [loadingTestimonials, setLoadingTestimonials] = useState(true);
  const [loadingRetailers, setLoadingRetailers] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [testimonialsData, retailersData] = await Promise.all([
          apiService.getTestimonials(),
          apiService.getRetailers(),
        ]);
        setTestimonials(testimonialsData);
        setRetailers(retailersData);
      } catch (error) {
        console.error('Erro ao carregar dados:', error);
      } finally {
        setLoadingTestimonials(false);
        setLoadingRetailers(false);
      }
    }
    fetchData();
  }, []);

  const sampleProducts = [
    {
      name: 'Notebook Gamer 15,6"',
      description: 'Tela Full HD 144 Hz · Ryzen 7 · 16 GB RAM · SSD 512 GB · RTX 4060',
      query: 'notebook gamer 15 rtx 4060 16gb ssd 512gb',
      price: 3500,
      retailerSlug: 'amazon',
      retailerName: 'Amazon',
      delivery: 2,
    },
    {
      name: 'Monitor 27" 4K',
      description: 'IPS 3840×2160 · 60 Hz · HDR10 · HDMI 2.0 e DisplayPort · altura ajustável',
      query: 'monitor 27 polegadas 4k ips hdr10',
      price: 1800,
      retailerSlug: 'mercado-livre',
      retailerName: 'Mercado Livre',
      delivery: 5,
    },
    {
      name: 'Teclado Mecânico RGB',
      description: 'ABNT2 · switch blue · anti-ghosting · retroiluminação RGB · cabo destacável',
      query: 'teclado mecanico rgb abnt2 switch blue',
      price: 450,
      retailerSlug: 'shopee',
      retailerName: 'Shopee',
      delivery: 3,
    },
  ];

  const retailerBySlug = new Map(retailers.map((retailer) => [retailer.slug, retailer]));

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-white">
      {/* Hero */}
      <section className="page-container text-center py-16">
        <h1 className="text-5xl font-bold text-gray-900 mb-6">
          Compare Preços de Produtos em um Único Lugar
        </h1>
        <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
          COBECO reúne preços de vários varejistas para você encontrar a melhor oferta. Crie
          listas, cotize produtos e economize tempo e dinheiro.
        </p>
        <div className="flex gap-4 justify-center">
          <a href="/sign-up" className="btn-primary text-lg">
            Começar Agora
          </a>
          <a href="#como-funciona" className="btn-secondary text-lg">
            Saiba Mais
          </a>
        </div>
      </section>

      {/* Como Funciona */}
      <section id="como-funciona" className="page-container py-16 bg-white rounded-lg shadow-md">
        <h2 className="text-3xl font-bold text-gray-900 mb-12 text-center">Como Funciona</h2>
        <div className="grid md:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="text-4xl font-bold text-primary-600 mb-4">1</div>
            <h3 className="text-xl font-semibold mb-2">Cadastre-se</h3>
            <p className="text-gray-600">Crie sua conta com e-mail e senha</p>
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold text-primary-600 mb-4">2</div>
            <h3 className="text-xl font-semibold mb-2">Monte Listas</h3>
            <p className="text-gray-600">Adicione produtos que deseja comparar</p>
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold text-primary-600 mb-4">3</div>
            <h3 className="text-xl font-semibold mb-2">Compare Preços</h3>
            <p className="text-gray-600">Veja os melhores preços e prazos de entrega</p>
          </div>
        </div>
      </section>

      {/* Exemplo de Produtos */}
      <section className="page-container py-16">
        <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">Exemplo de Dados</h2>
        {loadingRetailers ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-gray-100">
                  <th className="border border-gray-300 px-4 py-2 text-left font-semibold">
                    Produto
                  </th>
                  <th className="border border-gray-300 px-4 py-2 text-left font-semibold">
                    Varejista
                  </th>
                  <th className="border border-gray-300 px-4 py-2 text-right font-semibold">
                    Preço
                  </th>
                  <th className="border border-gray-300 px-4 py-2 text-center font-semibold">
                    Entrega (dias)
                  </th>
                </tr>
              </thead>
              <tbody>
                {sampleProducts.map((product) => {
                  const retailer = retailerBySlug.get(product.retailerSlug);
                  const productUrl = buildProductUrl(
                    product.retailerSlug,
                    product.query,
                    retailer?.websiteUrl
                  );
                  return (
                    <tr key={product.name} className="hover:bg-gray-50">
                      <td className="border border-gray-300 px-4 py-2">
                        <a
                          href={productUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-bold text-primary-700 underline hover:text-primary-800"
                          aria-label={`Ver ${product.name} em ${retailer?.name || product.retailerName} (abre em nova aba)`}
                        >
                          {product.name}
                        </a>
                        <br />
                        <span className="text-sm text-gray-600">{product.description}</span>
                      </td>
                      <td className="border border-gray-300 px-4 py-2">
                        <a
                          href={retailer?.websiteUrl || productUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary-700 underline hover:text-primary-800"
                        >
                          {retailer?.name || product.retailerName}
                        </a>
                      </td>
                      <td className="border border-gray-300 px-4 py-2 text-right">
                        R$ {product.price.toLocaleString('pt-BR')}
                      </td>
                      <td className="border border-gray-300 px-4 py-2 text-center">
                        {product.delivery}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <p className="mt-3 text-sm text-gray-500">
              Preços e prazos são ilustrativos. Os links abrem a busca do produto no site do
              lojista, em uma nova aba.
            </p>
          </div>
        )}
      </section>

      {/* Depoimentos */}
      <section className="page-container py-16">
        <h2 className="text-3xl font-bold text-gray-900 mb-12 text-center">O que Nossos Usuários Dizem</h2>
        {loadingTestimonials ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          </div>
        ) : (
          <div className="grid md:grid-cols-3 gap-8">
            {testimonials.map((testimonial) => (
              <div key={testimonial.id} className="card">
                <p className="text-gray-600 mb-4 italic">"{testimonial.content}"</p>
                <p className="font-semibold text-gray-900">— {testimonial.authorName}</p>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* CTA Final */}
      <section className="page-container py-16 text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-6">Pronto para Começar?</h2>
        <a href="/sign-up" className="btn-primary text-lg inline-block">
          Cadastre-se Gratuitamente
        </a>
      </section>
    </div>
  );
}
