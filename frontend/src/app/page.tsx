"use client";

import type { FormEvent, KeyboardEvent } from "react";
import { useEffect, useRef, useState } from "react";

type Message = {
  id: number;
  role: "user" | "assistant";
  content: string;
};

function cleanAssistantText(raw: string): string {
  let text = raw;

  if (text.startsWith('"')) {
    text = text.slice(1);
  }
  if (text.endsWith('"')) {
    text = text.slice(0, -1);
  }

  return text.replace(/\\n/g, "\n");
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({
        behavior: "smooth",
        block: "end",
      });
    }
  }, [messages, isLoading]);

  async function sendMessage(userText: string) {
    const trimmed = userText.trim();
    if (!trimmed || isLoading) return;

    setInput("");

    const userMessage: Message = {
      id: Date.now(),
      role: "user",
      content: trimmed,
    };

    const assistantMessage: Message = {
      id: Date.now() + 1,
      role: "assistant",
      content: "",
    };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setIsLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: trimmed }),
      });

      if (!response.body) {
        throw new Error("No response body");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulated = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        if (!value) continue;

        accumulated += decoder.decode(value, { stream: true });
        const cleaned = cleanAssistantText(accumulated);

        setMessages((prev) => {
          const next = [...prev];
          const index = next.findIndex(
            (message) =>
              message.role === "assistant" &&
              message.id === assistantMessage.id,
          );
          if (index !== -1) {
            next[index] = {
              ...next[index],
              content: cleaned,
            };
          }
          return next;
        });
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 2,
          role: "assistant",
          content: "There was an error talking to the backend.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!input.trim() || isLoading) return;
    await sendMessage(input);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (!isLoading && input.trim()) {
        void sendMessage(input);
      }
    }
  }

  const QUICK_PROMPTS = [
    "Plan a 10-day trip to Japan in April",
    "Budget weekend getaway in Europe",
    "Best beaches for snorkeling in SE Asia",
  ];

  const PlaneIcon = () => (
    <svg
      width="15"
      height="15"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  );

  const GlobeIcon = ({ size = 20 }: { size?: number }) => (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="12" cy="12" r="10" />
      <line x1="2" y1="12" x2="22" y2="12" />
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
    </svg>
  );

  const SparkleIcon = () => (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6z" />
    </svg>
  );

  return (
    <div className="flex h-screen justify-center bg-stone-100 px-4 py-4 overflow-hidden">
      <main className="flex w-full max-w-3xl flex-1 flex-col min-h-0">
        {/* Header */}
        <header className="mb-5 flex items-center justify-between border-b border-stone-200 pb-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-neutral-900 text-white">
              <GlobeIcon size={18} />
            </div>
            <div>
              <h1 className="text-[21px] font-semibold tracking-tight text-neutral-900">
                Travel Intelligence
              </h1>
              <p className="text-base text-stone-400">
                Your AI-powered trip planner
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1.5 rounded-full border border-stone-200 bg-white px-3 py-1.5 text-base text-stone-400">
            <SparkleIcon />
            <span>AI-powered</span>
          </div>
        </header>

        {/* Chat window */}
        <section className="flex flex-1 min-h-0 flex-col overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm">
          {/* Messages */}
          <div className="flex flex-1 min-h-0 flex-col gap-5 overflow-y-auto p-6">
            {messages.length === 0 ? (
              <div className="flex flex-1 flex-col items-center justify-center gap-3 py-12 text-center">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-stone-200 bg-stone-50 text-stone-400">
                  <GlobeIcon size={22} />
                </div>
                <p className="text-xl font-semibold tracking-tight text-neutral-900">
                  Where to next?
                </p>
                <p className="max-w-[260px] text-lg leading-relaxed text-stone-400">
                  Share your destination, dates, budget, and the kind of
                  experience you're after.
                </p>
                <div className="mt-2 flex flex-wrap justify-center gap-2">
                  {QUICK_PROMPTS.map((p) => (
                    <button
                      key={p}
                      onClick={() => sendMessage(p)}
                      className="rounded-full border border-stone-200 bg-stone-50 px-3.5 py-1.5 text-base text-stone-500 transition-colors hover:border-stone-300 hover:bg-stone-100 hover:text-neutral-800"
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg) => {
                if (msg.role === "assistant" && !msg.content.trim()) {
                  return null;
                }

                return (
                  <div
                    key={msg.id}
                    className={`flex items-end gap-2.5 ${
                      msg.role === "user" ? "flex-row-reverse" : "flex-row"
                    }`}
                  >
                    {/* Avatar — assistant only */}
                    {msg.role === "assistant" && (
                      <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg border border-stone-200 bg-stone-50 text-stone-400">
                        <GlobeIcon size={14} />
                      </div>
                    )}

                    <div
                      className={`max-w-[72%] rounded-2xl px-4 py-3 text-lg leading-relaxed ${
                        msg.role === "user"
                          ? "rounded-br-sm bg-neutral-900 text-white"
                          : "rounded-bl-sm border border-stone-200 bg-stone-50 text-neutral-900"
                      }`}
                    >
                      <p
                        className={`mb-1 text-[14px] font-semibold uppercase tracking-widest ${
                          msg.role === "user"
                            ? "text-white/50"
                            : "text-stone-400"
                        }`}
                      >
                        {msg.role === "user" ? "You" : "Assistant"}
                      </p>
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    </div>
                  </div>
                );
              })
            )}

            {/* Typing indicator */}
            {isLoading && (
              <div className="flex items-end gap-2.5">
                <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg border border-stone-200 bg-stone-50 text-stone-400">
                  <GlobeIcon size={14} />
                </div>
                <div className="rounded-2xl rounded-bl-sm border border-stone-200 bg-stone-50 px-4 py-3.5">
                  <div className="flex gap-1">
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-stone-400 [animation-delay:-0.3s]" />
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-stone-400 [animation-delay:-0.15s]" />
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-stone-400" />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input bar */}
          <form
            onSubmit={handleSubmit}
            className="flex items-end gap-2.5 border-t border-stone-200 bg-stone-50 px-4 py-3.5"
          >
            <textarea
              ref={textareaRef}
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about destinations, itineraries, costs…"
              className="flex-1 resize-none overflow-hidden rounded-xl border border-stone-200 bg-white px-3.5 py-2.5 text-lg text-neutral-900 placeholder:text-stone-300 outline-none transition-colors focus:border-stone-400"
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              aria-label="Send message"
              className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl bg-neutral-900 text-white transition-all hover:opacity-80 active:scale-95 disabled:cursor-not-allowed disabled:opacity-30"
            >
              <PlaneIcon />
            </button>
          </form>
        </section>
      </main>
    </div>
  );
}

// ─────────────────────────────────────
// 🌍 TRIP OVERVIEW
// ─────────────────────────────────────
// Embark on an unforgettable 10-day adventure to Japan in April 2026, during the enchanting cherry blossom season. This trip offers a harmony of cultural experiences, culinary delights, and breathtaking landscapes. Expect to witness the iconic sakura blooming, vibrant street food in Tokyo, and serene temple visits in historic Kyoto. Get ready for immersive activities that celebrate Japan's rich traditions and modern marvels.

// ─────────────────────────────────────
// ✈️ HOW TO GET THERE
// ─────────────────────────────────────
// The best mode of transport from Mumbai to Japan is by **flight**. This option is optimal due to its convenience and relatively short travel time, taking approximately **8-10 hours** on a direct route to major Japanese airports such as Narita (Tokyo) or Kansai (Osaka).

// Practical booking tips include:
// 1. **Book in advance** to secure better fares as prices can increase closer to the travel date.
// 2. Utilize online travel platforms like Expedia or Skyscanner to compare options and check for non-stop flights.
// 3. Ensure a baggage allowance of **20-30 kg** is included, which is common, but always verify specific airline policies.

// ─────────────────────────────────────
// 🗓️ DAY-BY-DAY ITINERARY
// ─────────────────────────────────────

// ### Day 1 — Arrival in Tokyo: Welcome to the Land of the Rising Sun

// **Morning**
// - **Activity name**: Arrive in Tokyo
// - **What to do**: Check into your hotel and freshen up after your flight. Take a leisurely stroll to acclimate yourself to the vibrant city.
// - **Why it's great**: This initial exploration will help you shake off travel fatigue and get inspired for your journey.
// - **Getting there**: Use the Narita Express train or airport limousine bus to reach central Tokyo efficiently.

// **Afternoon**
// - **Activity name**: Savor Tokyo Street Food
// - **What to do**: Head to the bustling districts of Shibuya and Tsukiji. Sample local delicacies like takoyaki (fried octopus balls) or okonomiyaki (savory pancakes).
// - **Why it's great**: Immerse yourself in Tokyo’s vibrant food scene, discovering authentic flavors that represent Japanese culture.
// - **Getting there**: Take the subway or walk to explore the nearby food stalls.

// **Evening**
// - **Activity name**: Visit Ueno Park for Hanami
// - **What to do**: Join locals in Ueno Park to partake in hanami, the traditional Japanese custom of flower viewing during cherry blossom season.
// - **Why it's great**: Experience the beauty of the cherry blossoms while enjoying picnics and festivities, marking a quintessential Japanese springtime experience.
// - **Getting there**: Ueno Park is easily accessible via the metro.

// **🍽️ Meal of the Day**
// - **Dish or experience**: Try takoyaki
// - **Where to try it**: Street stalls around Tsukiji Market
// - **Why you must try it**: This beloved street food offers a taste of local life and is a fun, social eat.

// ### Day 2 — Cultural Wonders of Kyoto

// **Morning**
// - **Activity name**: Explore Kyoto's Temples
// - **What to do**: Visit Kinkaku-ji (Golden Pavilion) and the impressive Fushimi Inari-taisha shrine with its iconic torii gates.
// - **Why it's great**: These sites represent the pinnacle of Japanese architecture and culture, revealing the spiritual heart of Kyoto.
// - **Getting there**: Take the Shinkansen (bullet train) from Tokyo to Kyoto, which is a quick and comfortable journey.

// **Afternoon**
// - **Activity name**: Stroll through the Arashiyama Bamboo Grove
// - **What to do**: Wander through the serene bamboo groves in Arashiyama, soaking in the tranquil atmosphere.
// - **Why it's great**: The towering bamboo stalks provide a magical setting ideal for photography and reflection.
// - **Getting there**: A short train or bus ride from central Kyoto will take you there.

// **Evening**
// - **Activity name**: Engage in a Tea Ceremony
// - **What to do**: Participate in a traditional tea ceremony in Uji, known for its matcha (green tea).
// - **Why it's great**: Gain insight into Japanese customs and appreciate the artistry involved in this ritual.
// - **Getting there**: A train ride from Kyoto to Uji makes it an easy excursion.

// **🍽️ Meal of the Day**
// - **Dish or experience**: Kaiseki dining
// - **Where to try it**: A local ryokan or traditional restaurant in Kyoto
// - **Why you must try it**: Experience a multi-course Japanese meal that showcases seasonal ingredients and culinary artistry.

// ### Day 3 — History of Hiroshima and Miyajima

// **Morning**
// - **Activity name**: Visit Hiroshima Peace Memorial Park
// - **What to do**: Explore the memorial park and museum dedicated to the victims of the atomic bombing of Hiroshima.
// - **Why it's great**: The poignant exhibits remind visitors of the importance of peace and human resilience.
// - **Getting there**: Take the Shinkansen from Kyoto to Hiroshima.

// **Afternoon**
// - **Activity name**: Ferry to Miyajima Island
// - **What to do**: Take a ferry from Hiroshima to Miyajima Island to see the famous torii gate of Itsukushima Shrine.
// - **Why it's great**: This iconic sight offers breathtaking views, especially with the backdrop of cherry blossoms.
// - **Getting there**: Ferries run frequently from Hiroshima's port.

// **Evening**
// - **Activity name**: Return and evening in Hiroshima
// - **What to do**: Explore the city’s lively downtown area, trying local delicacies like Hiroshima-style okonomiyaki.
// - **Why it's great**: Enjoy the blend of history and modernity that Hiroshima exudes, along with its unique culinary offerings.
// - **Getting there**: Walk or take a streetcar from the Peace Memorial Park to downtown.

// **🍽️ Meal of the Day**
// - **Dish or experience**: Hiroshima-style okonomiyaki
// - **Where to try it**: Local okonomiyaki restaurants.
// - **Why you must try it**: This variation of the savory pancake is a must-try, layered with flavors unique to Hiroshima.

// ### Day 4 — Scenic Serenity in Hakone

// **Morning**
// - **Activity name**: Travel to Hakone
// - **What to do**: Head to Hakone for stunning views of Mt. Fuji. Check into a ryokan (traditional inn).
// - **Why it's great**: Experience the tranquility and beauty of Japan's natural landscapes along with luxurious hospitality.
// - **Getting there**: Take the Shinkansen from Hiroshima to Odawara Station, then transfer to the Hakone Tozan Railway.

// **Afternoon**
// - **Activity name**: Relaxing Onsen Experience
// - **What to do**: Unwind in an onsen (hot spring) and enjoy the rejuvenating properties of the mineral waters.
// - **Why it's great**: This embodies the Japanese art of relaxation and refreshment, surrounded by beautiful scenery.
// - **Getting there**: Most ryokans have their own onsen facilities.

// **Evening**
// - **Activity name**: Kaiseki Dinner at Ryokan
// - **What to do**: Enjoy a multi-course dinner highlighting seasonal ingredients.
// - **Why it's great**: It provides a deep dive into the fine art of Japanese cooking and the cultural significance behind each dish.
// - **Getting there**: Served within your ryokan.

// **🍽️ Meal of the Day**
// - **Dish or experience**: Traditional Kaiseki
// - **Where to try it**: Your ryokan
// - **Why you must try it**: It’s a culinary journey showcasing seasonal ingredients and exquisite presentation.

// ### Day 5 — Majestic Views and Mountain Adventures

// **Morning**
// - **Activity name**: Hike Mount Fuji
// - **What to do**: Take a day trip to hike the base of Mount Fuji or explore surrounding areas for breathtaking views.
// - **Why it's great**: This iconic mountain is not only a national symbol but hiking among cherry blossoms can be uniquely beautiful.
// - **Getting there**: Use local buses or trains to reach the 5th Station of Mount Fuji.

// **Afternoon**
// - **Activity name**: Explore Fuji Five Lakes
// - **What to do**: Spend time around one of the Five Lakes near Mount Fuji, enjoying the scenic views and perhaps a short hike.
// - **Why it's great**: The combination of lakes and blossoms provides a picturesque setting perfect for photography.
// - **Getting there**: Local buses connect you to the area from Mount Fuji.

// **Evening**
// - **Activity name**: Return to Hakone
// - **What to do**: Journey back to Hakone in the evening, perhaps taking a scenic lake cruise if time permits.
// - **Why it's great**: Reflect on your awe-inspiring day in the shadow of Mount Fuji.
// - **Getting there**: Public transport services direct routes back to Hakone.

// **🍽️ Meal of the Day**
// - **Dish or experience**: Yuba (tofu skin)
// - **Where to try it**: A local restaurant in the Hakone area
// - **Why you must try it**: This unique delicacy is a highlight of the region’s cuisine and a must-try for food enthusiasts.

// ### Day 6 — Nara's Cultural Richness

// **Morning**
// - **Activity name**: Visit Nara Park
// - **What to do**: Experience Nara Park, home to free-roaming deer and historical sites like Todai-ji Temple.
// - **Why it's great**: This area combines stunning nature with rich history.
// - **Getting there**: Take a train from Hakone to Nara, which may involve a transfer.

// **Afternoon**
// - **Activity name**: Explore Todai-ji Temple
// - **What to do**: Visit Todai-ji, which houses a giant Buddha statue and is a UNESCO World Heritage site.
// - **Why it's great**: This temple is a masterpiece of traditional Japanese architecture and an important cultural site.
// - **Getting there**: A short walk from Nara Park.

// **Evening**
// - **Activity name**: Evening stroll through Naramachi
// - **What to do**: Wander the historic streets of Naramachi, lined with traditional wooden houses and shops.
// - **Why it's great**: Experience an authentic slice of old Japan and perhaps pick up some local crafts.
// - **Getting there**: A leisurely walk from Todai-ji.

// **🍽️ Meal of the Day**
// - **Dish or experience**: Kakinoha-zushi (persimmon leaf sushi)
// - **Where to try it**: Local eateries in Nara
// - **Why you must try it**: This regional sushi variety offers a unique taste and presentation, encapsulating the local culture.

// ### Day 7 — Back to the Future in Tokyo

// **Morning**
// - **Activity name**: Arrival back in Tokyo
// - **What to do**: Travel back to the heart of Tokyo and check into your hotel.
// - **Why it's great**: Return to a dynamic city filled with modern marvels alongside traditional culture.
// - **Getting there**: Ride the Shinkansen from Nara back to Tokyo.

// **Afternoon**
// - **Activity name**: Explore Akihabara
// - **What to do**: Dive into Akihabara, the tech district, filled with electronics shops, anime stores, and maid cafes.
// - **Why it's great**: This place embodies otaku culture and showcases Japan's love for technology and entertainment.
// - **Getting there**: Accessible via the Tokyo Metro.

// **Evening**
// - **Activity name**: Evening at Shinjuku
// - **What to do**: Explore the vibrant nightlife of Shinjuku, from dazzling lights to izakayas (Japanese pubs).
// - **Why it's great**: Shinjuku provides a lively atmosphere perfect for experiencing contemporary Japanese culture.
// - **Getting there**: A short train ride from Akihabara.

// **🍽️ Meal of the Day**
// - **Dish or experience**: Ramen
// - **Where to try it**: Popular ramen shops in Shinjuku.
// - **Why you must try it**: Indulging in a warm bowl of ramen is a comforting experience and an essential part of Japanese cuisine.

// ### Day 8 — Leisure and Luxury in Tokyu’s Oasis

// **Morning**
// - **Activity name**: Visit the Meiji Shrine
// - **What to do**: Start your day with a visit to the peaceful Meiji Shrine, a Shinto shrine surrounded by a tranquil forest.
// - **Why it's great**: This site offers a serene escape from the city’s hustle and a glimpse into Japan's spiritual life.
// - **Getting there**: Easily reached via a short walk from Harajuku Station.

// **Afternoon**
// - **Activity name**: Shopping in Harajuku
// - **What to do**: Discover the unique fashion scene of Harajuku, exploring its trendy shops and boutiques.
// - **Why it's great**: The eclectic style of Harajuku captures contemporary Japanese fashion trends and culture.
// - **Getting there**: Walk from the Meiji Shrine into the main shopping district.

// **Evening**
// - **Activity name**: Rooftop Views at Roppongi Hills
// - **What to do**: Head to the Roppongi Hills observation deck for panoramic views of Tokyo at sunset.
// - **Why it's great**: Witnessing the expansive city lights at dusk creates a magical end to your day.
// - **Getting there**: A subway ride to Roppongi Station will get you there quickly.

// **🍽️ Meal of the Day**
// - **Dish or experience**: Wagyu beef
// - **Where to try it**: Upscale dining in Roppongi.
// - **Why you must try it**: Enjoying a meal of this premium beef is a once-in-a-lifetime culinary experience.

// ### Day 9 — Adventure and Art in the City

// **Morning**
// - **Activity name**: Explore the National Art Center
// - **What to do**: Visit the National Art Center, Tokyo, which features rotating exhibits from contemporary Japanese and international artists.
// - **Why it's great**: This museum allows for a unique look into the ever-evolving art scene without a permanent exhibit.
// - **Getting there**: Easily accessible via subway to Roppongi.

// **Afternoon**
// - **Activity name**: Explore the Tokyo Tower
// - **What to do**: Visit the Tokyo Tower for breathtaking city views and explore its interesting exhibitions.
// - **Why it's great**: This symbol of Tokyo offers an impressive panorama, especially when new blossoms peek through the skyline.
// - **Getting there**: A short metro ride from the national art center.

// **Evening**
// - **Activity name**: Enjoy Tokyo Bay Cruise
// - **What to do**: Take a relaxing cruise around Tokyo Bay, which offers stunning views of the city from the water.
// - **Why it's great**: This experience provides a unique perspective of Tokyo’s skyline, with lights sparkling against the water at dusk.
// - **Getting there**: Head to the Tokyo Bay cruise terminal via subway.

// **🍽️ Meal of the Day**
// - **Dish or experience**: Tempura
// - **Where to try it**: A popular tempura restaurant near Tokyo Tower.
// - **Why you must try it**: The light, crispy batter used in tempura represents a classic Japanese cooking technique that is a must-try.

// ### Day 10 — Departure and Reflection

// **Morning**
// - **Activity name**: Last-minute Shopping
// - **What to do**: Spend your final hours in Tokyo shopping for souvenirs in areas like Ginza or Shibuya.
// - **Why it's great**: This opportunity allows you to bring back pieces of Japan, from cultural artifacts to unique artworks.
// - **Getting there**: Take the subway to either Ginza or Shibuya.

// **Afternoon**
// - **Activity name**: Enjoy a Farewell Meal
// - **What to do**: Have a farewell lunch at a local favorite eatery, indulging in your favorite Japanese dish one last time.
// - **Why it's great**: This meal allows for reflection on your beautiful experiences throughout Japan.
// - **Getting there**: Choose a restaurant within walking distance in your chosen shopping area.

// **Evening**
// - **Activity name**: Departure from Japan
// - **What to do**: Head to the airport for your flight back to Mumbai.
// - **Why it's great**: Depart with a heart full of memories, having truly experienced the beauty of Japanese culture.
// - **Getting there**: Utilize the airport Limousine service or express trains based on your location.

// **🍽️ Meal of the Day**
// - **Dish or experience**: Sushi
// - **Where to try it**: A sushi train or local sushi bar.
// - **Why you must try it**: Finishing your culinary adventure with sushi encapsulates the essence of Japanese cuisine.

// ─────────────────────────────────────
// 🌤️ TIMING & SEASONAL ADVICE
// ─────────────────────────────────────
// April 2026 falls within **peak season** in Japan, a time when cherry blossoms are in full bloom, enhancing the scenic beauty and cultural experiences. Visitors will gain the opportunity to enjoy vibrant hanami festivals, picnics, and festivities in parks, along with mild spring weather perfect for exploring. However, they may miss out on reduced prices and less crowded attractions typically associated with off-peak seasons. To make the most of this vibrant time, consider booking popular attractions in advance to avoid long lines.

// ─────────────────────────────────────
// 💡 ESSENTIAL TRAVEL TIPS
// ─────────────────────────────────────
// - **Check Visa Requirements**: Become familiar with Japan’s visa policies well in advance of your trip to avoid any last-minute surprises.
// - **Carry Local Currency**: While major establishments accept credit cards, many small shops and food stalls only take cash, so ensure you have enough yen on hand.
// - **Use Public Transport**: Japan’s public transport system is efficient and extensive. Consider purchasing a Japan Rail Pass for seamless travel across cities.
// - **Respect Local Customs**: Learn basic Japanese customs, such as bowing as a form of greeting, to enhance your experience and show respect to locals.
// - **Pack Layered Clothing**: Spring temperatures can be variable, so pack layers to stay comfortable when experiencing different weather throughout the day.

// ─────────────────────────────────────
// 📋 QUICK REFERENCE SUMMARY
// ─────────────────────────────────────
// - **Destination**     : Japan
// - **Traveling from**  : Mumbai
// - **Travel date**     : April 2026
// - **Duration**        : 10 days
// - **Best transport**  : Flight (direct from Mumbai to Tokyo/Osaka)
// - **Season**          : Peak
// - **Top 3 highlights**: Participate in hanami, Experience a traditional tea ceremony, Visit Hiroshima Peace Memorial Park.
