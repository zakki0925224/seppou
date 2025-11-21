import { CaretDownOutlined, CopyOutlined, HeartOutlined, MessageOutlined, RetweetOutlined } from "@ant-design/icons";
import { Avatar, Button, Collapse, Space, Typography } from "antd";
import { useEffect, useState } from "react";

const { Panel } = Collapse;
const { Text, Paragraph } = Typography;

export interface User {
    name: string;
    username: string;
    avatarUrl?: string;
}

export interface TweetData {
    id: number;
    user: User;
    content: string;
    detail: string;
    timestamp: Date;
}

function formatRelativeTime(date: Date): string {
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diffInSeconds < 60) {
        return `${diffInSeconds}秒前`;
    } else if (diffInSeconds < 3600) {
        const minutes = Math.floor(diffInSeconds / 60);
        return `${minutes}分前`;
    } else if (diffInSeconds < 86400) {
        const hours = Math.floor(diffInSeconds / 3600);
        return `${hours}時間前`;
    } else {
        const days = Math.floor(diffInSeconds / 86400);
        return `${days}日前`;
    }
}

const Tweet = ({ user, content, detail, timestamp }: Readonly<TweetData>) => {
    const [relativeTime, setRelativeTime] = useState(formatRelativeTime(timestamp));
    const [copySuccess, setCopySuccess] = useState(false);

    const handleCopy = async () => {
        try {
            const object = { user, content, detail, timestamp };
            await navigator.clipboard.writeText(JSON.stringify(object, null, 2));
            setCopySuccess(true);
            setTimeout(() => setCopySuccess(false), 2000);
        } catch (err) {
            console.error("Failed to copy:", err);
        }
    };

    useEffect(() => {
        const updateRelativeTime = () => setRelativeTime(formatRelativeTime(timestamp));
        updateRelativeTime();

        const interval = setInterval(updateRelativeTime, 60000);
        return () => clearInterval(interval);
    }, [timestamp])

    return (
        <div
            style={{
                width: "100%",
                borderTop: "1px solid #f0f0f0",
                borderBottom: "1px solid #f0f0f0",
                padding: "16px",
                boxSizing: "border-box",
            }}
        >
            <div style={{ display: "flex", alignItems: "flex-start", gap: "12px" }}>
                <Avatar size={48} src={user.avatarUrl} />

                <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "4px" }}>
                    <Space size={8} align="center">
                        <Text strong>{user.name}</Text>
                        <Text type="secondary">@{user.username}</Text>
                        <Text type="secondary">·</Text>
                        <Text type="secondary">{relativeTime}</Text>
                    </Space>

                    <Paragraph
                        style={{
                            wordBreak: "break-word",
                            overflowWrap: "break-word",
                            marginBottom: 0,
                        }}
                    >
                        {content}
                    </Paragraph>
                </div>
            </div>

            <div
                style={{
                    display: "flex",
                    justifyContent: "space-around",
                    paddingTop: "8px",
                    width: "100%",
                }}
            >
                <Button type="text" icon={<MessageOutlined style={{ fontSize: "18px" }} />} />
                <Button type="text" icon={<RetweetOutlined style={{ fontSize: "18px" }} />} />
                <Button type="text" icon={<HeartOutlined style={{ fontSize: "18px" }} />} />
                <Button
                    type="text"
                    icon={<CopyOutlined style={{ fontSize: "18px" }} />}
                    onClick={handleCopy}
                    title="コピー"
                    style={{
                        color: copySuccess ? "#52c41a" : "inherit",
                    }}
                />
            </div>

            <Collapse
                bordered={false}
                defaultActiveKey={[""]}
                expandIcon={({ isActive }) => <CaretDownOutlined rotate={isActive ? 180 : 0} />}
                style={{
                    backgroundColor: "transparent",
                    marginTop: "8px",
                    padding: 0,
                }}
            >
                <Panel
                    key="detail"
                    header={<Text type="secondary" style={{ fontSize: "14px" }}>Prompts</Text>}
                    showArrow={true}
                    style={{
                        border: "none",
                        padding: 0,
                        backgroundColor: "transparent",
                    }}
                    extra={null}
                >
                    <div
                        style={{
                            backgroundColor: "#fafafa",
                            borderRadius: "4px",
                            padding: "12px",
                        }}
                    >
                        <Paragraph
                            type="secondary"
                            style={{
                                whiteSpace: "pre-wrap",
                                wordBreak: "break-word",
                                marginBottom: 0,
                            }}
                        >
                            {detail}
                        </Paragraph>
                    </div>
                </Panel>
            </Collapse>
        </div>
    )
}

export const TimeLine = ({ tweets }: Readonly<{ tweets: TweetData[] }>) => {
    useEffect(() => {
        console.log("[Timeline] Received tweets:", tweets.length);
    }, [tweets]);

    return (
        <div
            style={{
                width: "100%",
                height: "100vh",
                display: "flex",
                flexDirection: "column",
                overflow: "hidden",
            }}
        >
            <div
                style={{
                    overflowY: "auto",
                    overflowX: "hidden",
                    flex: 1,
                }}
            >
                <div style={{ display: "flex", flexDirection: "column" }}>
                    {tweets.map((tweet) => (
                        <Tweet key={tweet.id} {...tweet} />
                    ))}
                </div>
            </div>
        </div>
    );
}

export default TimeLine;
