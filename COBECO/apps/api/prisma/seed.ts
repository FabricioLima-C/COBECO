import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

const products = [
  ['product-1', 'Arroz 5 kg'],
  ['product-2', 'Feijão 1 kg'],
  ['product-3', 'Óleo de soja 900 ml'],
  ['product-4', 'Açúcar 1 kg'],
  ['product-5', 'Café 500 g'],
  ['product-6', 'Leite integral 1 L'],
  ['product-7', 'Farinha de trigo 1 kg'],
  ['product-8', 'Macarrão 500 g'],
  ['product-9', 'Sal 1 kg'],
  ['product-10', 'Produto sem oferta'],
] as const;

const coverage: Record<string, number[]> = {
  A: [1, 2, 3, 4, 5, 6, 7, 8, 9],
  B: [1, 2, 3, 4, 5, 6, 7, 8, 9],
  C: [1, 2, 3, 4, 5, 6, 8, 9],
  D: [1, 2, 4, 5, 8, 9],
  E: [1, 2, 3, 4, 5, 6, 8, 9],
  F: [1, 2, 3, 4, 5, 6, 8, 9],
  G: [1, 3, 4, 5, 8, 9],
  H: [1, 2, 3, 4, 5, 6, 8, 9],
};

async function main() {
  const category = await prisma.category.upsert({
    where: { name: 'Supermercado' },
    update: {},
    create: { id: 'supermercado', name: 'Supermercado' },
  });

  for (const [id, name] of products) {
    await prisma.product.upsert({
      where: { id },
      update: { name, categoryId: category.id, active: true },
      create: { id, name, categoryId: category.id },
    });
  }

  for (const [supplierIndex, [letter, productNumbers]] of Object.entries(coverage).entries()) {
    const supplierId = `supplier-${letter.toLowerCase()}`;
    await prisma.supplier.upsert({
      where: { id: supplierId },
      update: { name: `Fornecedor ${letter}`, active: true },
      create: { id: supplierId, name: `Fornecedor ${letter}`, categoryId: category.id },
    });
    for (const productNumber of productNumbers) {
      await prisma.supplierProduct.upsert({
        where: { supplierId_productId: { supplierId, productId: `product-${productNumber}` } },
        update: { price: 5 + productNumber + supplierIndex, active: true },
        create: {
          supplierId,
          productId: `product-${productNumber}`,
          price: 5 + productNumber + supplierIndex,
          active: true,
        },
      });
    }
  }

  await prisma.supplierProduct.upsert({
    where: { supplierId_productId: { supplierId: 'supplier-h', productId: 'product-10' } },
    update: { price: 99, active: false },
    create: { supplierId: 'supplier-h', productId: 'product-10', price: 99, active: false },
  });

  const retailers = [
    ['amazon', 'Amazon', 'https://www.amazon.com.br'],
    ['mercado-livre', 'Mercado Livre', 'https://www.mercadolivre.com.br'],
    ['shopee', 'Shopee', 'https://www.shopee.com.br'],
    ['magazine-luiza', 'Magazine Luiza', 'https://www.magazineluiza.com.br'],
  ];
  for (const [slug, name, websiteUrl] of retailers) {
    await prisma.retailer.upsert({
      where: { slug },
      update: {},
      create: { slug, name, websiteUrl },
    });
  }

  const testimonials = [
    [
      'testimonial-1',
      'João Silva',
      'O COBECO tornou a comparação da minha compra muito mais simples.',
    ],
    [
      'testimonial-2',
      'Maria Santos',
      'Os grupos de cobertura deixam claro onde encontro todos os produtos.',
    ],
    ['testimonial-3', 'Carlos Oliveira', 'Consigo ver rapidamente o orçamento mais econômico.'],
  ];
  for (const [id, authorName, content] of testimonials) {
    await prisma.testimonial.upsert({
      where: { id },
      update: {},
      create: { id, authorName, content, approved: true },
    });
  }
}

main()
  .then(() => console.log('Seed concluído: catálogo A-H e dados públicos carregados.'))
  .catch((error) => {
    console.error(error);
    process.exitCode = 1;
  })
  .finally(() => prisma.$disconnect());
