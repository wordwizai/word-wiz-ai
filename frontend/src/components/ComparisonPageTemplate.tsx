import React from "react";
import { Helmet } from "react-helmet-async";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Link } from "react-router-dom";
import { Check, X, Star, ArrowRight, Info } from "lucide-react";
import LandingPageNavbar from "@/components/LandingPageNavbar";
import LandingPageFooter from "@/components/LandingPageFooter";

interface ComparisonProduct {
  name: string;
  logo?: string;
  tagline: string;
  pricing: {
    free: string;
    paid?: string;
    trial?: string;
  };
  rating: number;
  reviewCount: number;
  website: string;
}

interface ComparisonFeature {
  category: string;
  features: {
    name: string;
    product1: boolean | string;
    product2: boolean | string;
    wordWiz: boolean | string;
  }[];
}

interface ProsConsItem {
  text: string;
}

interface ProductDetails {
  pros: ProsConsItem[];
  cons: ProsConsItem[];
  bestFor: string[];
  description: string;
}

interface FAQItem {
  question: string;
  answer: string;
}

interface ComparisonPageProps {
  product1: ComparisonProduct;
  product2: ComparisonProduct;
  wordWiz: ComparisonProduct;
  comparisonFeatures: ComparisonFeature[];
  product1Details: ProductDetails;
  product2Details: ProductDetails;
  wordWizDetails: ProductDetails;
  metaTitle: string;
  metaDescription: string;
  h1Title: string;
  introText: string;
  verdict: {
    product1: string;
    product2: string;
    wordWiz: string;
    overall: string;
  };
  faqs: FAQItem[];
  structuredData: any;
}

const ComparisonPage: React.FC<ComparisonPageProps> = ({
  product1,
  product2,
  wordWiz,
  comparisonFeatures,
  product1Details,
  product2Details,
  wordWizDetails,
  metaTitle,
  metaDescription,
  h1Title,
  introText,
  verdict,
  faqs,
  structuredData,
}) => {
  const renderValue = (value: boolean | string) => {
    if (typeof value === "boolean") {
      return value ? (
        <Check className="w-5 h-5 text-green-600 mx-auto" />
      ) : (
        <X className="w-5 h-5 text-muted-foreground/40 mx-auto" />
      );
    }
    return (
      <span className="text-sm text-center text-muted-foreground">{value}</span>
    );
  };

  return (
    <>
      <Helmet>
        <title>{metaTitle}</title>
        <meta name="description" content={metaDescription} />
        <meta property="og:title" content={metaTitle} />
        <meta property="og:description" content={metaDescription} />
        <meta property="og:type" content="article" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content={metaTitle} />
        <meta name="twitter:description" content={metaDescription} />
        <script type="application/ld+json">
          {JSON.stringify(structuredData)}
        </script>
      </Helmet>

      <div className="min-h-screen flex flex-col bg-background">
        <LandingPageNavbar />

        <main className="flex-1 container mx-auto px-4 py-12 max-w-7xl">
          {/* Header */}
          <div className="text-center mb-12">
            <Badge variant="outline" className="mb-4">
              <Info className="w-3 h-3 mr-1" />
              Comparison Guide
            </Badge>
            <h1 className="text-3xl md:text-5xl font-bold mb-4 text-foreground">
              {h1Title}
            </h1>
            <p className="text-base md:text-lg text-muted-foreground max-w-3xl mx-auto">
              {introText}
            </p>
          </div>

          {/* Quick Comparison Table */}
          <Card className="mb-12 border-2">
            <CardHeader>
              <CardTitle className="text-xl md:text-2xl">
                Quick Comparison at a Glance
              </CardTitle>
              <CardDescription>
                Compare key features side-by-side
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-muted">
                    <tr>
                      <th className="text-left p-3 md:p-4 font-semibold text-sm md:text-base">
                        Feature
                      </th>
                      <th className="text-center p-3 md:p-4 font-semibold text-sm md:text-base">
                        {product1.name}
                      </th>
                      <th className="text-center p-3 md:p-4 font-semibold text-sm md:text-base">
                        {product2.name}
                      </th>
                      <th className="text-center p-3 md:p-4 font-semibold text-sm md:text-base">
                        {wordWiz.name}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-t">
                      <td className="p-3 md:p-4 font-medium text-sm md:text-base">
                        Starting Price
                      </td>
                      <td className="p-3 md:p-4 text-center text-sm md:text-base text-muted-foreground">
                        {product1.pricing.paid || product1.pricing.free}
                      </td>
                      <td className="p-3 md:p-4 text-center text-sm md:text-base text-muted-foreground">
                        {product2.pricing.paid || product2.pricing.free}
                      </td>
                      <td className="p-3 md:p-4 text-center font-semibold text-sm md:text-base">
                        {wordWiz.pricing.free}
                      </td>
                    </tr>
                    <tr className="border-t">
                      <td className="p-3 md:p-4 font-medium text-sm md:text-base">
                        Free Tier
                      </td>
                      <td className="p-3 md:p-4 text-center text-sm md:text-base">
                        {product1.pricing.trial || "Limited"}
                      </td>
                      <td className="p-3 md:p-4 text-center text-sm md:text-base">
                        {product2.pricing.trial || "Limited"}
                      </td>
                      <td className="p-3 md:p-4 text-center">
                        <Check className="w-5 h-5 text-green-600 mx-auto" />
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Detailed Feature Comparison */}
          {comparisonFeatures.map((category, idx) => (
            <Card key={idx} className="mb-8">
              <CardHeader>
                <CardTitle className="text-lg md:text-xl">
                  {category.category}
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-muted">
                      <tr>
                        <th className="text-left p-2 md:p-3 font-medium text-xs md:text-sm">
                          Feature
                        </th>
                        <th className="text-center p-2 md:p-3 font-medium text-xs md:text-sm">
                          {product1.name}
                        </th>
                        <th className="text-center p-2 md:p-3 font-medium text-xs md:text-sm">
                          {product2.name}
                        </th>
                        <th className="text-center p-2 md:p-3 font-medium text-xs md:text-sm">
                          {wordWiz.name}
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {category.features.map((feature, featureIdx) => (
                        <tr
                          key={featureIdx}
                          className="border-t hover:bg-muted/30 transition-colors"
                        >
                          <td className="p-2 md:p-3 text-xs md:text-sm">
                            {feature.name}
                          </td>
                          <td className="p-2 md:p-3 text-center">
                            {renderValue(feature.product1)}
                          </td>
                          <td className="p-2 md:p-3 text-center">
                            {renderValue(feature.product2)}
                          </td>
                          <td className="p-2 md:p-3 text-center">
                            {renderValue(feature.wordWiz)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          ))}

          {/* Pros and Cons Section */}
          <div className="mb-12">
            <h2 className="text-2xl md:text-3xl font-bold mb-6 text-center">
              Detailed Analysis
            </h2>
            <div className="grid md:grid-cols-3 gap-6">
              {/* Product 1 */}
              <Card className="border-2">
                <CardHeader>
                  <CardTitle className="text-lg md:text-xl">
                    {product1.name}
                  </CardTitle>
                  <CardDescription className="text-xs md:text-sm">
                    {product1.tagline}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-6">
                  <div className="mb-6">
                    <h4 className="font-semibold text-green-700 mb-3 flex items-center gap-2 text-sm md:text-base">
                      <Check className="w-4 h-4" />
                      Pros
                    </h4>
                    <ul className="space-y-2">
                      {product1Details.pros.map((pro, idx) => (
                        <li
                          key={idx}
                          className="text-xs md:text-sm flex items-start gap-2"
                        >
                          <span className="text-green-600 mt-0.5">✓</span>
                          <span>{pro.text}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <Separator className="my-4" />
                  <div className="mb-6">
                    <h4 className="font-semibold text-red-700 mb-3 flex items-center gap-2 text-sm md:text-base">
                      <X className="w-4 h-4" />
                      Cons
                    </h4>
                    <ul className="space-y-2">
                      {product1Details.cons.map((con, idx) => (
                        <li
                          key={idx}
                          className="text-xs md:text-sm flex items-start gap-2 text-muted-foreground"
                        >
                          <span className="text-red-500 mt-0.5">✗</span>
                          <span>{con.text}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <Separator className="my-4" />
                  <div>
                    <h4 className="font-semibold mb-3 text-sm md:text-base">
                      Best For:
                    </h4>
                    <ul className="space-y-1.5">
                      {product1Details.bestFor.map((item, idx) => (
                        <li
                          key={idx}
                          className="text-xs md:text-sm text-muted-foreground flex items-start gap-2"
                        >
                          <ArrowRight className="w-3 h-3 mt-0.5 text-primary flex-shrink-0" />
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </CardContent>
              </Card>

              {/* Product 2 */}
              <Card className="border-2">
                <CardHeader>
                  <CardTitle className="text-lg md:text-xl">
                    {product2.name}
                  </CardTitle>
                  <CardDescription className="text-xs md:text-sm">
                    {product2.tagline}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-6">
                  <div className="mb-6">
                    <h4 className="font-semibold text-green-700 mb-3 flex items-center gap-2 text-sm md:text-base">
                      <Check className="w-4 h-4" />
                      Pros
                    </h4>
                    <ul className="space-y-2">
                      {product2Details.pros.map((pro, idx) => (
                        <li
                          key={idx}
                          className="text-xs md:text-sm flex items-start gap-2"
                        >
                          <span className="text-green-600 mt-0.5">✓</span>
                          <span>{pro.text}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <Separator className="my-4" />
                  <div className="mb-6">
                    <h4 className="font-semibold text-red-700 mb-3 flex items-center gap-2 text-sm md:text-base">
                      <X className="w-4 h-4" />
                      Cons
                    </h4>
                    <ul className="space-y-2">
                      {product2Details.cons.map((con, idx) => (
                        <li
                          key={idx}
                          className="text-xs md:text-sm flex items-start gap-2 text-muted-foreground"
                        >
                          <span className="text-red-500 mt-0.5">✗</span>
                          <span>{con.text}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <Separator className="my-4" />
                  <div>
                    <h4 className="font-semibold mb-3 text-sm md:text-base">
                      Best For:
                    </h4>
                    <ul className="space-y-1.5">
                      {product2Details.bestFor.map((item, idx) => (
                        <li
                          key={idx}
                          className="text-xs md:text-sm text-muted-foreground flex items-start gap-2"
                        >
                          <ArrowRight className="w-3 h-3 mt-0.5 text-primary flex-shrink-0" />
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </CardContent>
              </Card>

              {/* Word Wiz AI */}
              <Card className="border-2 border-primary shadow-lg">
                <CardHeader>
                  <div className="flex items-center justify-between mb-2">
                    <Badge variant="default">Recommended</Badge>
                  </div>
                  <CardTitle className="text-lg md:text-xl">
                    {wordWiz.name}
                  </CardTitle>
                  <CardDescription className="text-xs md:text-sm">
                    {wordWiz.tagline}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-6">
                  <div className="mb-6">
                    <h4 className="font-semibold text-green-700 mb-3 flex items-center gap-2 text-sm md:text-base">
                      <Check className="w-4 h-4" />
                      Pros
                    </h4>
                    <ul className="space-y-2">
                      {wordWizDetails.pros.map((pro, idx) => (
                        <li
                          key={idx}
                          className="text-xs md:text-sm flex items-start gap-2 font-medium"
                        >
                          <span className="text-green-600 mt-0.5">✓</span>
                          <span>{pro.text}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <Separator className="my-4" />
                  <div className="mb-6">
                    <h4 className="font-semibold text-red-700 mb-3 flex items-center gap-2 text-sm md:text-base">
                      <X className="w-4 h-4" />
                      Cons
                    </h4>
                    <ul className="space-y-2">
                      {wordWizDetails.cons.map((con, idx) => (
                        <li
                          key={idx}
                          className="text-xs md:text-sm flex items-start gap-2 text-muted-foreground"
                        >
                          <span className="text-red-500 mt-0.5">✗</span>
                          <span>{con.text}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <Separator className="my-4" />
                  <div className="mb-6">
                    <h4 className="font-semibold mb-3 text-sm md:text-base">
                      Best For:
                    </h4>
                    <ul className="space-y-1.5">
                      {wordWizDetails.bestFor.map((item, idx) => (
                        <li
                          key={idx}
                          className="text-xs md:text-sm text-muted-foreground flex items-start gap-2"
                        >
                          <ArrowRight className="w-3 h-3 mt-0.5 text-primary flex-shrink-0" />
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <Button className="w-full" size="lg" asChild>
                    <Link to="/signup">
                      Sign Up Free
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Link>
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>

          {/* Verdict Section */}
          <Card className="mb-12 border-2">
            <CardHeader>
              <CardTitle className="text-xl md:text-2xl">
                Final Verdict: Which Should You Choose?
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6 space-y-6">
              <div className="space-y-2">
                <h3 className="font-semibold text-base md:text-lg">
                  {product1.name}
                </h3>
                <p className="text-sm md:text-base text-muted-foreground leading-relaxed">
                  {verdict.product1}
                </p>
              </div>
              <Separator />
              <div className="space-y-2">
                <h3 className="font-semibold text-base md:text-lg">
                  {product2.name}
                </h3>
                <p className="text-sm md:text-base text-muted-foreground leading-relaxed">
                  {verdict.product2}
                </p>
              </div>
              <Separator />
              <div className="bg-muted p-4 md:p-6 rounded-lg border-2 border-primary">
                <div className="flex items-center gap-2 mb-3">
                  <Badge variant="default">Our Recommendation</Badge>
                </div>
                <h3 className="font-bold text-base md:text-lg mb-3">
                  {wordWiz.name}
                </h3>
                <p className="text-sm md:text-base text-muted-foreground mb-4 leading-relaxed">
                  {verdict.wordWiz}
                </p>
                <p className="text-sm md:text-base font-semibold text-foreground leading-relaxed">
                  {verdict.overall}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* FAQ Section */}
          <Card className="mb-12 border-2">
            <CardHeader>
              <CardTitle className="text-xl md:text-2xl">
                Frequently Asked Questions
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="space-y-6">
                {faqs.map((faq, idx) => (
                  <div key={idx}>
                    <h3 className="font-semibold text-sm md:text-base mb-2 text-primary">
                      {faq.question}
                    </h3>
                    <p className="text-xs md:text-sm text-muted-foreground leading-relaxed">
                      {faq.answer}
                    </p>
                    {idx < faqs.length - 1 && <Separator className="mt-6" />}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* CTA */}
          <Card className="border-2 border-primary">
            <CardContent className="text-center py-8 md:py-12 px-4">
              <Badge variant="default" className="mb-4">
                Free Forever
              </Badge>
              <h2 className="text-2xl md:text-3xl font-bold mb-4 text-foreground">
                Ready to Experience AI-Powered Reading Instruction?
              </h2>
              <p className="text-sm md:text-lg text-muted-foreground mb-6 max-w-2xl mx-auto leading-relaxed">
                Join Word Wiz AI free today and discover the power of
                phoneme-level pronunciation feedback for your child.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button size="lg" asChild>
                  <Link to="/signup">
                    Get Started Free
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Link>
                </Button>
                <Button size="lg" variant="outline" asChild>
                  <Link to="/about">Learn More</Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        </main>

        <LandingPageFooter />
      </div>
    </>
  );
};

export default ComparisonPage;
