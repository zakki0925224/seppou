import { Flex } from "antd";
import { useEffect, useState } from "react";
import TimeLine, { type TweetData } from "./TimeLine";
import config from "../../config.toml";

export const App = () => {
    const [tweets, setTweets] = useState<TweetData[]>([]);

    useEffect(() => {
        const fetchAllTweets = async () => {
            try {
                const response = await fetch(
                    `${config.shiki.host}:${config.shiki.port}/tweet/`,
                );
                if (!response.ok) return;

                const result = await response.json();
                const dataList = result.data;

                if (Array.isArray(dataList)) {
                    const fetchedTweets: TweetData[] = dataList.map(
                        (data: any) => ({
                            id: data.doc_id,
                            user: {
                                name: "Shiki",
                                username: "shiki_bot",
                            },
                            content: data.tweet,
                            detail: `Thinking: ${data.generate_ms}ms\n${data.prompts}`,
                            timestamp: new Date(data.timestamp),
                        }),
                    );

                    setTweets(fetchedTweets.toReversed());
                }
            } catch (error) {
                console.error("Failed to fetch tweets:", error);
            }
        };

        fetchAllTweets();
        const interval = setInterval(
            fetchAllTweets,
            config.zen.polling_interval_ms,
        );
        return () => clearInterval(interval);
    }, []);

    return (
        <Flex gap="middle" wrap>
            <TimeLine tweets={tweets} />
        </Flex>
    );
};

export default App;
