import { Flex } from "antd";
import { useEffect, useState } from "react";
import TimeLine, { type TweetData } from "./TimeLine";

const SHIKI_API_URL = "http://localhost:8000";
const POLLING_INTERVAL = 10000;

export const App = () => {
    const [tweets, setTweets] = useState<TweetData[]>([]);
    const [lastTimestamp, setLastTimestamp] = useState<string | null>(null);

    useEffect(() => {
        const fetchLatestTweet = async () => {
            try {
                const response = await fetch(`${SHIKI_API_URL}/tweet/`);
                if (response.ok) {
                    const result = await response.json();
                    const data = result.data;

                    if (data.timestamp !== lastTimestamp) {
                        const newTweet: TweetData = {
                            user: {
                                name: "Shiki",
                                username: "shiki_bot",
                            },
                            content: data.tweet,
                            detail: `Thinking: ${data.generate_ms}ms\n${data.prompts}`,
                            timestamp: new Date(data.timestamp),
                        };

                        setTweets((prev) => [newTweet, ...prev]);
                        setLastTimestamp(data.timestamp);
                    }
                }
            } catch (error) {
                console.error("Failed to fetch tweet:", error);
            }
        };

        fetchLatestTweet();
        const interval = setInterval(fetchLatestTweet, POLLING_INTERVAL);
        return () => clearInterval(interval);
    }, [lastTimestamp]);

    return (
        <Flex gap="middle" wrap>
            <TimeLine tweets={tweets} />
        </Flex>
    );
};

export default App;
