import { Flex } from "antd";
import { useEffect, useState } from "react";
import TimeLine, { type TweetData } from "./TimeLine";

const SHIKI_API_URL = "http://localhost:8000";
const POLLING_INTERVAL = 10000;

export const App = () => {
    const [tweets, setTweets] = useState<TweetData[]>([]);

    useEffect(() => {
        const fetchAllTweets = async () => {
            try {
                const response = await fetch(`${SHIKI_API_URL}/tweet/`);
                if (!response.ok) return;

                const result = await response.json();
                const dataList = result.data;

                if (Array.isArray(dataList)) {
                    const fetchedTweets: TweetData[] = dataList.map((data: any) => ({
                        id: data.doc_id,
                        user: {
                            name: "Shiki",
                            username: "shiki_bot",
                        },
                        content: data.tweet,
                        detail: `Thinking: ${data.generate_ms}ms\n${data.prompts}`,
                        timestamp: new Date(data.timestamp),
                    }));

                    setTweets(fetchedTweets.toReversed());
                }
            } catch (error) {
                console.error("Failed to fetch tweets:", error);
            }
        };

        fetchAllTweets();
        const interval = setInterval(fetchAllTweets, POLLING_INTERVAL);
        return () => clearInterval(interval);
    }, []);

    return (
        <Flex gap="middle" wrap>
            <TimeLine tweets={tweets} />
        </Flex>
    );
};

export default App;
